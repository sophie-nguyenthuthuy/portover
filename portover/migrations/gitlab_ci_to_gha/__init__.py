""".gitlab-ci.yml (GitLab CI) -> GitHub Actions workflow.

Two structural differences drive this migration:

- **Stages.** GitLab orders work with a global `stages:` list: everything in a
  stage runs in parallel, and the next stage waits. GHA has no stages, only
  per-job `needs:`. So the driver wires each job to the previous non-empty
  stage — unless the job declared its own `needs:`, which is already a DAG and
  maps across directly.
- **Templates.** Hidden `.jobs` plus `extends:` are GitLab's reuse mechanism.
  GHA has no job inheritance, so templates are merged into their consumers and
  never emitted themselves.

Everything else is per-directive and lives in mappings/.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from portover.core import Migration, Report, load_mappings
from portover.emit import yaml_dump
from portover.miniyaml import MiniYamlError, parse

CONFIG_PATHS = (".gitlab-ci.yml", ".gitlab-ci.yaml")

# Top-level keys that configure the pipeline; anything else is a job definition.
GLOBAL_KEYS = {"stages", "types", "variables", "default", "include", "workflow",
               "image", "services", "before_script", "after_script", "cache"}

DEFAULT_STAGES = ["build", "test", "deploy"]

_CI_VAR = re.compile(r"\$\{?(CI_[A-Z0-9_]+|GITLAB_CI)\}?")


@dataclass
class GitlabContext:
    stages: list = field(default_factory=lambda: list(DEFAULT_STAGES))
    variables: dict = field(default_factory=dict)
    defaults: dict = field(default_factory=dict)  # image/services/cache/before_script/...
    templates: dict = field(default_factory=dict)  # ".name" -> definition
    jobs: dict = field(default_factory=dict)  # jid -> GHA job
    job_stage: dict = field(default_factory=dict)  # jid -> stage name
    job_order: list = field(default_factory=list)
    explicit_needs: set = field(default_factory=set)
    current_jid: str = ""  # job being converted, for mappings that must name it
    scripts: dict = field(default_factory=dict)  # current job: before/main/after
    on: dict = field(default_factory=dict)
    concurrency: dict = field(default_factory=dict)
    used_ci_vars: set = field(default_factory=set)


def slug(name: str) -> str:
    s = re.sub(r"[^a-z0-9_-]+", "-", str(name).lower()).strip("-")
    if not s:
        return "job"
    return s if s[0].isalpha() or s[0] == "_" else f"job-{s}"


def as_list(value):
    if value is None:
        return []
    return list(value) if isinstance(value, list) else [value]


def scoped(scope: str) -> list:
    return [m for m in load_mappings(GitlabCiToGha.package)
            if getattr(m, "SCOPE", "pipeline") == scope]


def note_ci_vars(text, ctx) -> None:
    """Record which GitLab predefined variables a script actually uses."""
    if isinstance(text, str):
        ctx.used_ci_vars.update(_CI_VAR.findall(text))


def merge(base: dict, override: dict) -> dict:
    """GitLab's extends merge: dicts merge key-wise, everything else replaces."""
    out = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = merge(out[key], value)
        else:
            out[key] = value
    return out


def minutes(value) -> int | None:
    """GitLab durations: '1h 30m', '90 minutes', '30m'."""
    text = str(value).strip().lower()
    total, found = 0, False
    for amount, unit in re.findall(r"(\d+(?:\.\d+)?)\s*([a-z]*)", text):
        if not amount:
            continue
        n = float(amount)
        if unit.startswith("h"):
            total += n * 60
        elif unit.startswith("s"):
            total += n / 60
        elif unit.startswith("d"):
            total += n * 1440
        else:  # bare number or minutes
            total += n
        found = True
    return max(1, int(round(total))) if found else None


class GitlabCiToGha(Migration):
    id = "gitlab-ci-to-gha"
    source = ".gitlab-ci.yml (GitLab CI)"
    target = ".github/workflows/*.yml (GitHub Actions)"
    package = "portover.migrations.gitlab_ci_to_gha"

    def detect(self, root) -> list[str]:
        root = Path(root)
        return [p for p in CONFIG_PATHS if (root / p).exists()]

    def run(self, root) -> Report:
        root = Path(root)
        report = Report(self.id)
        found = self.detect(root)
        try:
            doc = parse((root / found[0]).read_text())
        except MiniYamlError as e:
            report.manual("parse", found[0],
                          f"config uses YAML features portover's reader skips ({e}) — "
                          "expand anchors/aliases (or use `extends:`, which portover does resolve) and retry")
            return report
        if not isinstance(doc, dict):
            report.manual("parse", found[0], "expected a top-level mapping")
            return report

        ctx = GitlabContext()
        keys = list(doc)
        for m in scoped("pipeline"):
            for key in [k for k in keys if m.matches(k)]:
                m.apply(key, doc[key], ctx, report)
                keys.remove(key)
        for key in keys:
            report.unmapped.append(f"{found[0]}: {key}")

        if not ctx.jobs:
            report.manual("jobs", found[0], "no job definitions found to convert")
            return report

        self.wire_stages(ctx, report)
        report.outputs[".github/workflows/ci.yml"] = yaml_dump(self.assemble(ctx, report)) + "\n"
        return report

    def wire_stages(self, ctx: GitlabContext, report: Report) -> None:
        """GitLab stages are sequential; express that as needs: on the previous stage."""
        by_stage: dict = {}
        for jid in ctx.job_order:
            by_stage.setdefault(ctx.job_stage.get(jid, "test"), []).append(jid)
        known = [s for s in ctx.stages if s in by_stage]
        for stage in by_stage:
            if stage not in known:
                report.manual("stages", f"stage: {stage}",
                              "stage is not in the `stages:` list — jobs kept unordered; add needs: by hand")
        for i, stage in enumerate(known):
            if i == 0:
                continue
            previous = by_stage[known[i - 1]]
            for jid in by_stage[stage]:
                if jid in ctx.explicit_needs:
                    continue
                ctx.jobs[jid]["needs"] = previous if len(previous) > 1 else previous[0]

    def assemble(self, ctx: GitlabContext, report: Report) -> dict:
        from portover.migrations.gitlab_ci_to_gha.mappings import ci_variables

        workflow: dict = {"name": "CI", "on": ctx.on or self.default_on()}
        if ctx.concurrency:
            workflow["concurrency"] = ctx.concurrency
        env = dict(ctx.variables)
        env.update(ci_variables.compat_env(ctx, report))
        if env:
            workflow["env"] = env
        workflow["jobs"] = {jid: order_job(ctx.jobs[jid]) for jid in ctx.job_order}
        return workflow

    @staticmethod
    def default_on() -> dict:
        return {"push": {}, "pull_request": {}}


_JOB_ORDER = ["name", "needs", "if", "runs-on", "environment", "concurrency", "permissions",
              "container", "services", "strategy", "env", "defaults", "timeout-minutes",
              "continue-on-error", "steps"]


def order_job(job: dict) -> dict:
    return dict(sorted(job.items(),
                       key=lambda kv: (_JOB_ORDER.index(kv[0]) if kv[0] in _JOB_ORDER
                                       else len(_JOB_ORDER), kv[0])))


MIGRATION = GitlabCiToGha()
