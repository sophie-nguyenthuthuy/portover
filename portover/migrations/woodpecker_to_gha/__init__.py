""".woodpecker.yml (Woodpecker CI) -> GitHub Actions workflow.

Woodpecker began as a Drone fork and shares its best idea — steps are
containers sharing one workspace volume, which is GHA *step* behaviour — so a
Woodpecker workflow becomes a GHA job and its steps become that job's steps.

Where it has since diverged is what this migration actually has to handle:

- `steps:` may be a LIST (each with `name:`) or a MAP (name -> step);
- `when:` is a LIST of condition sets, OR'd together, not a single map;
- `environment:` may be a map or a list of `KEY=value` strings;
- there is a real `matrix:`, which maps onto `strategy.matrix`;
- variables are `CI_*`, not Drone's `DRONE_*`;
- a repo may hold several workflow files under `.woodpecker/`, wired to each
  other with `depends_on:` — those become several jobs in one workflow.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from portover.core import Migration, Report, load_mappings
from portover.emit import yaml_dump
from portover.miniyaml import MiniYamlError, parse

SINGLE_FILES = (".woodpecker.yml", ".woodpecker.yaml")
WORKFLOW_DIR = ".woodpecker"
WORKSPACE = "/woodpecker/src"

_VAR = re.compile(r"\$\{?(CI_[A-Z0-9_]+)\}?")
_INTERP = re.compile(r"\$\{?([A-Za-z_][A-Za-z0-9_]*)\}?")


@dataclass
class WoodpeckerContext:
    jobs: dict = field(default_factory=dict)
    job_order: list = field(default_factory=list)
    names: dict = field(default_factory=dict)  # workflow name -> job id
    depends: dict = field(default_factory=dict)  # job id -> [workflow name]
    on: dict = field(default_factory=dict)
    used_vars: set = field(default_factory=set)
    current_jid: str = ""
    matrix_keys: set = field(default_factory=set)
    plain_push: bool = False  # a push event was asked for, not only tags
    # per-step scratch, set by the steps mapping before each step's fields run
    step_image: str = ""
    step_shared_image: bool = True
    step_env: dict = field(default_factory=dict)


def slug(name: str) -> str:
    s = re.sub(r"[^a-z0-9_-]+", "-", str(name).lower()).strip("-")
    s = re.sub(r"-{2,}", "-", s)
    if not s:
        return "workflow"
    return s if s[0].isalpha() or s[0] == "_" else f"job-{s}"


def as_list(value):
    if value is None:
        return []
    return list(value) if isinstance(value, list) else [value]


def scoped(scope: str) -> list:
    return [m for m in load_mappings(WoodpeckerToGha.package)
            if getattr(m, "SCOPE", "pipeline") == scope]


def note_vars(text, ctx) -> None:
    if isinstance(text, str):
        ctx.used_vars.update(_VAR.findall(text))


def as_env(value, ctx=None) -> dict:
    """Woodpecker environment is a map OR a list of KEY=value strings."""
    out: dict = {}
    if isinstance(value, dict):
        for name, spec in value.items():
            out[str(name)] = spec
    else:
        for entry in as_list(value):
            text = str(entry)
            if "=" in text:
                name, _, spec = text.partition("=")
                out[name.strip()] = spec.strip()
    return out


def interpolate_matrix(text, ctx):
    """`golang:${GO_VERSION}` -> `golang:${{ matrix.GO_VERSION }}` for matrix keys."""
    if not isinstance(text, str) or not ctx.matrix_keys:
        return text

    def replace(match):
        name = match.group(1)
        return "${{ matrix.%s }}" % name if name in ctx.matrix_keys else match.group(0)

    return _INTERP.sub(replace, text)


def normalize_steps(value, report) -> list:
    """Accept both the list form and the map form of `steps:`."""
    if isinstance(value, dict):
        entries = []
        for name, spec in value.items():
            if isinstance(spec, dict):
                entries.append({"name": str(name), **spec})
        return entries
    return [s for s in as_list(value) if isinstance(s, dict)]


class WoodpeckerToGha(Migration):
    id = "woodpecker-to-gha"
    source = ".woodpecker.yml (Woodpecker CI)"
    target = ".github/workflows/*.yml (GitHub Actions)"
    package = "portover.migrations.woodpecker_to_gha"

    def detect(self, root) -> list[str]:
        root = Path(root)
        found = [p for p in SINGLE_FILES if (root / p).exists()]
        directory = root / WORKFLOW_DIR
        if directory.is_dir():
            found.extend(sorted(f"{WORKFLOW_DIR}/{p.name}" for p in directory.iterdir()
                                if p.suffix in (".yml", ".yaml")))
        return found

    def run(self, root) -> Report:
        root = Path(root)
        report = Report(self.id)
        ctx = WoodpeckerContext()
        for relative in self.detect(root):
            try:
                document = parse((root / relative).read_text())
            except MiniYamlError as e:
                report.manual("parse", relative,
                              f"config uses YAML features portover's reader skips ({e}) — "
                              "Woodpecker configs often use anchors under `variables:`; expand them and retry")
                continue
            if not isinstance(document, dict) or not document:
                continue
            self.convert(document, ctx, report, relative=relative)

        if not ctx.jobs:
            if not report.hits:
                report.manual("steps", ".woodpecker.yml", "no steps found to convert")
            return report

        self.wire(ctx, report)
        report.outputs[".github/workflows/ci.yml"] = yaml_dump(self.assemble(ctx, report)) + "\n"
        return report

    def convert(self, document: dict, ctx: WoodpeckerContext, report: Report, *, relative: str) -> None:
        name = Path(relative).stem.lstrip(".") or "workflow"
        jid = slug(name)
        while jid in ctx.jobs:
            jid = f"{jid}-{len(ctx.job_order)}"
        ctx.names[name] = jid
        ctx.current_jid = jid
        ctx.matrix_keys = set()

        job: dict = {"runs-on": "ubuntu-latest"}
        ctx.depends[jid] = [str(d) for d in as_list(document.get("depends_on"))]

        pipeline_maps = scoped("pipeline")
        # matrix first: later fields interpolate ${VAR} against its keys
        fields = sorted(document.items(), key=lambda kv: 0 if kv[0] == "matrix" else 1)
        for field_name, spec in fields:
            if field_name == "depends_on":
                continue
            for m in pipeline_maps:
                if m.matches(field_name):
                    m.apply(field_name, spec, job, ctx, report)
                    break
            else:
                report.unmapped.append(f"{relative}: {field_name}")

        steps: list = [] if job.pop("_no_checkout", False) else [_checkout(job)]
        steps.extend(job.pop("_steps", []))
        job["steps"] = steps
        if not steps:
            report.manual("steps", relative, "workflow has no steps — add its commands by hand")
        ctx.jobs[jid] = job
        ctx.job_order.append(jid)
        report.mapped("workflow", f"{relative}", f"job '{jid}' ({len(steps)} steps)")

    def wire(self, ctx: WoodpeckerContext, report: Report) -> None:
        for jid, parents in ctx.depends.items():
            needs = [ctx.names.get(p, slug(p)) for p in parents]
            needs = [n for n in needs if n in ctx.jobs and n != jid]
            if needs:
                ctx.jobs[jid]["needs"] = needs if len(needs) > 1 else needs[0]
                report.mapped("workflow-depends", f"{jid} depends_on {parents}", f"needs: {needs}")

    def assemble(self, ctx: WoodpeckerContext, report: Report) -> dict:
        from portover.migrations.woodpecker_to_gha.mappings import ci_variables

        _fix_push_filters(ctx)
        workflow: dict = {"name": "CI", "on": ctx.on or {"push": {}, "pull_request": {}}}
        env = ci_variables.compat_env(ctx, report)
        if env:
            workflow["env"] = env
        workflow["jobs"] = {jid: order_job(ctx.jobs[jid]) for jid in ctx.job_order}
        return workflow


def _fix_push_filters(ctx) -> None:
    """`on: push: tags:` alone means ONLY tags trigger — branch pushes stop building."""
    push = ctx.on.get("push")
    if ctx.plain_push and isinstance(push, dict) and push.get("tags") and not push.get("branches"):
        push["branches"] = ["**"]


def _checkout(job: dict) -> dict:
    checkout: dict = {"uses": "actions/checkout@v4"}
    with_ = job.pop("_checkout_with", None)
    if with_:
        checkout["with"] = with_
    return checkout


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


MIGRATION = WoodpeckerToGha()
