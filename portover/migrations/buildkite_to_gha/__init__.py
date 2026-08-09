"""Buildkite pipeline.yml -> GitHub Actions workflow.

Buildkite and GHA agree on the thing most CI systems disagree about: steps run
concurrently unless you say otherwise. So the interesting translation is the
*barrier*. Buildkite orders work with a bare `- wait` between steps, meaning
"everything above finishes before anything below starts"; GHA has no barrier at
all, only per-job `needs:`. The driver therefore tracks the steps in the current
barrier group and, at each `wait`, makes every following step depend on all of
them — which reproduces the ordering exactly.

`depends_on:` is the other half: it references step `key:`s and maps straight
onto `needs:`, overriding the barrier for that step the way Buildkite does.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from portover.core import Migration, Report, load_mappings
from portover.emit import yaml_dump
from portover.miniyaml import MiniYamlError, parse

CONFIG_PATHS = (".buildkite/pipeline.yml", ".buildkite/pipeline.yaml",
                "buildkite.yml", "buildkite.yaml", "pipeline.yml")

_VAR = re.compile(r"\$\{?(BUILDKITE_[A-Z0-9_]+|CI)\}?")
_MATRIX = re.compile(r"\{\{\s*matrix(?:\.([A-Za-z0-9_]+))?\s*\}\}")


@dataclass
class BuildkiteContext:
    env: dict = field(default_factory=dict)
    default_agents: dict = field(default_factory=dict)
    jobs: dict = field(default_factory=dict)
    job_order: list = field(default_factory=list)
    keys: dict = field(default_factory=dict)  # buildkite key -> gha job id
    barrier: list = field(default_factory=list)  # jobs since the last wait
    pending_needs: list = field(default_factory=list)  # what the next step must wait for
    used_vars: set = field(default_factory=set)
    current_jid: str = ""
    matrix_vars: set = field(default_factory=set)
    uses_agent_cli: bool = False
    provided_vars: set = field(default_factory=set)  # vars a mapping already defines


def slug(name: str) -> str:
    s = re.sub(r"[^a-z0-9_-]+", "-", str(name).lower()).strip("-")
    s = re.sub(r"-{2,}", "-", s)
    if not s:
        return "step"
    return s if s[0].isalpha() or s[0] == "_" else f"step-{s}"


def as_list(value):
    if value is None:
        return []
    return list(value) if isinstance(value, list) else [value]


def scoped(scope: str) -> list:
    return [m for m in load_mappings(BuildkiteToGha.package)
            if getattr(m, "SCOPE", "pipeline") == scope]


def note_vars(text, ctx) -> None:
    if isinstance(text, str):
        ctx.used_vars.update(_VAR.findall(text))
        if "buildkite-agent" in text:
            ctx.uses_agent_cli = True


def interpolate(text, ctx):
    """Rewrite Buildkite `{{matrix}}` / `{{matrix.key}}` into GHA matrix refs."""
    if not isinstance(text, str):
        return text

    def replace(match):
        key = match.group(1)
        return "${{ matrix.%s }}" % (key if key else "value")

    return _MATRIX.sub(replace, text)


def build_command_step(definition: dict, ctx: BuildkiteContext, report: Report,
                       *, index: int) -> tuple:
    """Convert one Buildkite command step into a GHA job."""
    label = str(definition.get("label") or definition.get("name")
                or definition.get("key") or f"step {index}")
    clean = _clean_label(label)  # ':docker: Build' -> 'Build', so the id is not 'docker-build'
    jid = slug(definition.get("key") or clean)
    while jid in ctx.jobs:
        jid = f"{jid}-{index}"

    job: dict = {"runs-on": "ubuntu-latest"}
    if clean != jid:
        job["name"] = clean
    ctx.current_jid = jid
    ctx.matrix_vars = set()

    if ctx.default_agents and "agents" not in definition:
        _apply("agents", ctx.default_agents, job, ctx, report)

    for field_name, spec in definition.items():
        if field_name in ("label", "name", "key"):
            continue
        _apply(field_name, spec, job, ctx, report)

    steps: list = [{"uses": "actions/checkout@v4"}]
    steps.extend(job.pop("_pre_steps", []))
    steps.extend(job.pop("_script", []))
    steps.extend(job.pop("_post_steps", []))
    job.pop("_artifacts", None)  # Buildkite has no implicit pass-through; nothing to wire
    job["steps"] = steps
    if not any("run" in s for s in steps):
        report.manual("command", label, "step has no command — add its commands by hand")
    return jid, job


def _apply(field_name, spec, job, ctx, report) -> None:
    for m in scoped("step"):
        if m.matches(field_name):
            m.apply(field_name, spec, job, ctx, report)
            return
    report.unmapped.append(f"step field: {field_name}")


_EMOJI = re.compile(r":[a-z0-9_+-]+:")


def _clean_label(label: str) -> str:
    """Buildkite labels are usually emoji-prefixed (':docker: Build')."""
    return _EMOJI.sub("", str(label)).strip() or str(label)


class BuildkiteToGha(Migration):
    id = "buildkite-to-gha"
    source = "Buildkite pipeline.yml"
    target = ".github/workflows/*.yml (GitHub Actions)"
    package = "portover.migrations.buildkite_to_gha"

    def detect(self, root) -> list[str]:
        root = Path(root)
        found = []
        for path in CONFIG_PATHS:
            candidate = root / path
            if not candidate.exists():
                continue
            if path == "pipeline.yml":  # too generic: only claim it if it looks like Buildkite
                try:
                    doc = parse(candidate.read_text())
                except MiniYamlError:
                    continue
                if not (isinstance(doc, dict) and "steps" in doc):
                    continue
            found.append(path)
        return found

    def run(self, root) -> Report:
        root = Path(root)
        report = Report(self.id)
        found = self.detect(root)
        try:
            doc = parse((root / found[0]).read_text())
        except MiniYamlError as e:
            report.manual("parse", found[0],
                          f"config uses YAML features portover's reader skips ({e}) — "
                          "expand anchors/aliases and retry")
            return report
        if not isinstance(doc, dict):
            report.manual("parse", found[0], "expected a top-level mapping")
            return report

        ctx = BuildkiteContext()
        keys = list(doc)
        for m in scoped("pipeline"):
            for key in [k for k in keys if m.matches(k)]:
                m.apply(key, doc[key], ctx, report)
                keys.remove(key)
        for key in keys:
            report.unmapped.append(f"{found[0]}: {key}")

        if not ctx.jobs:
            report.manual("steps", found[0], "no steps found to convert")
            return report

        report.outputs[".github/workflows/ci.yml"] = yaml_dump(self.assemble(ctx, report)) + "\n"
        return report

    def assemble(self, ctx: BuildkiteContext, report: Report) -> dict:
        from portover.migrations.buildkite_to_gha.mappings import variables as variables_map

        workflow: dict = {"name": "CI", "on": {"push": {}, "pull_request": {}}}
        env = dict(ctx.env)
        env.update(variables_map.compat_env(ctx, report))
        if env:
            workflow["env"] = env
        workflow["jobs"] = {jid: order_job(ctx.jobs[jid]) for jid in ctx.job_order}
        return workflow


_JOB_ORDER = ["name", "needs", "if", "runs-on", "environment", "concurrency", "permissions",
              "container", "services", "strategy", "env", "defaults", "timeout-minutes",
              "continue-on-error", "steps"]
_STEP_ORDER = ["name", "id", "if", "uses", "run", "shell", "with", "env",
               "working-directory", "continue-on-error", "timeout-minutes"]


def _ordered(mapping: dict, order: list) -> dict:
    return dict(sorted(mapping.items(),
                       key=lambda kv: (order.index(kv[0]) if kv[0] in order else len(order), kv[0])))


def order_job(job: dict) -> dict:
    job = _ordered(job, _JOB_ORDER)
    if isinstance(job.get("steps"), list):
        job["steps"] = [_ordered(s, _STEP_ORDER) if isinstance(s, dict) else s for s in job["steps"]]
    return job


MIGRATION = BuildkiteToGha()
