"""azure-pipelines.yml (Azure Pipelines) -> GitHub Actions workflow.

Azure nests three levels — stages > jobs > steps — and all three are optional:
a pipeline may be bare `steps:`, or `jobs:`, or the full `stages:` tree. GHA has
exactly one level (jobs with steps), so the driver flattens whatever it finds:

- `steps:` alone becomes a single job;
- `jobs:` map across directly, with `dependsOn` becoming `needs`;
- `stages:` are dissolved — a stage's entry jobs inherit `needs` from every job
  of the stages it depends on, which preserves the ordering exactly.

Job ids are prefixed with their stage only when two stages reuse a job name.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from portover.core import Migration, Report, load_mappings
from portover.emit import yaml_dump
from portover.miniyaml import MiniYamlError, parse

CONFIG_PATHS = ("azure-pipelines.yml", "azure-pipelines.yaml",
                ".azure-pipelines.yml", ".azure/azure-pipelines.yml")

_MACRO = re.compile(r"\$\((?P<name>[A-Za-z_][A-Za-z0-9_.]*)\)")


@dataclass
class AzureContext:
    variables: dict = field(default_factory=dict)  # workflow-level env
    declared: set = field(default_factory=set)  # variable names declared anywhere
    inputs: dict = field(default_factory=dict)  # workflow_dispatch inputs
    default_pool: dict = field(default_factory=dict)
    jobs: dict = field(default_factory=dict)  # jid -> GHA job
    job_order: list = field(default_factory=list)
    job_stage: dict = field(default_factory=dict)  # jid -> stage slug
    stage_jobs: dict = field(default_factory=dict)  # stage slug -> [jid]
    stage_depends: dict = field(default_factory=dict)  # stage slug -> [stage slug]
    stage_order: list = field(default_factory=list)
    job_depends: dict = field(default_factory=dict)  # jid -> [job name]
    on: dict = field(default_factory=dict)
    used_macros: set = field(default_factory=set)
    current_jid: str = ""
    matrix_vars: set = field(default_factory=set)  # matrix keys of the job being built


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
    return [m for m in load_mappings(AzurePipelinesToGha.package)
            if getattr(m, "SCOPE", "pipeline") == scope]


def rewrite_macros(text, ctx, report=None):
    """Rewrite Azure `$(Name)` macros, leaving shell command substitution alone.

    `$(Build.SourceVersion)` is an Azure macro, but `$(git rev-parse HEAD)` is
    bash command substitution — and in bash the former would try to *run* a
    command called Build.SourceVersion. So only names that are dotted (a
    predefined variable) or declared in this pipeline are rewritten; anything
    else is left untouched, which keeps real shell substitutions working.
    """
    from portover.migrations.azure_pipelines_to_gha.mappings import predefined_variables as pv

    if not isinstance(text, str):
        return text

    def replace(match):
        name = match.group("name")
        safe = name.replace(".", "_")
        if safe in ctx.matrix_vars:  # a matrix leg variable, not an env var
            return "${{ matrix.%s }}" % safe
        if "." in name or name in ctx.declared:
            ctx.used_macros.add(name)
            return pv.reference(name)
        return match.group(0)  # leave shell command substitution untouched

    return _MACRO.sub(replace, text)


class AzurePipelinesToGha(Migration):
    id = "azure-pipelines-to-gha"
    source = "azure-pipelines.yml (Azure Pipelines)"
    target = ".github/workflows/*.yml (GitHub Actions)"
    package = "portover.migrations.azure_pipelines_to_gha"

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
                          "expand anchors/aliases and retry")
            return report
        if not isinstance(doc, dict):
            report.manual("parse", found[0], "expected a top-level mapping")
            return report

        ctx = AzureContext()
        _predeclare(doc, ctx)
        keys = list(doc)
        for m in scoped("pipeline"):
            for key in [k for k in keys if m.matches(k)]:
                m.apply(key, doc[key], ctx, report)
                keys.remove(key)
        for key in keys:
            report.unmapped.append(f"{found[0]}: {key}")

        if not ctx.jobs:
            report.manual("jobs", found[0],
                          "no steps/jobs/stages found — nothing to convert")
            return report

        self.wire(ctx, report)
        report.outputs[".github/workflows/ci.yml"] = yaml_dump(self.assemble(ctx, report)) + "\n"
        return report

    def wire(self, ctx: AzureContext, report: Report) -> None:
        """dependsOn -> needs, at both job and stage level."""
        names = {name: jid for jid, name in
                 ((jid, ctx.jobs[jid].get("_source_name", jid)) for jid in ctx.job_order)}
        for jid in ctx.job_order:
            deps = [names.get(str(d), slug(str(d))) for d in ctx.job_depends.get(jid, [])]
            deps = [d for d in deps if d in ctx.jobs]
            if not deps:  # entry job: inherit the stage's dependencies
                stage = ctx.job_stage.get(jid)
                for parent in ctx.stage_depends.get(stage, []):
                    deps.extend(ctx.stage_jobs.get(parent, []))
            deps = [d for d in dict.fromkeys(deps) if d != jid]
            if deps:
                ctx.jobs[jid]["needs"] = deps if len(deps) > 1 else deps[0]
        for jid in ctx.job_order:
            ctx.jobs[jid].pop("_source_name", None)

    def assemble(self, ctx: AzureContext, report: Report) -> dict:
        from portover.migrations.azure_pipelines_to_gha.mappings import predefined_variables as pv

        workflow: dict = {"name": "CI", "on": ctx.on or self.default_on()}
        if ctx.inputs:
            workflow["on"].setdefault("workflow_dispatch", {})["inputs"] = ctx.inputs
        env = dict(ctx.variables)
        env.update(pv.compat_env(ctx, report))
        if env:
            workflow["env"] = env
        workflow["jobs"] = {jid: order_job(ctx.jobs[jid]) for jid in ctx.job_order}
        return workflow

    @staticmethod
    def default_on() -> dict:
        return {"push": {}, "pull_request": {}}


def _predeclare(doc: dict, ctx: AzureContext) -> None:
    """Collect declared variable names up front so macro rewriting can use them."""
    def walk(node):
        if isinstance(node, dict):
            variables = node.get("variables")
            if isinstance(variables, dict):
                ctx.declared.update(str(k) for k in variables)
            for entry in as_list(variables) if isinstance(variables, list) else []:
                if isinstance(entry, dict) and entry.get("name"):
                    ctx.declared.add(str(entry["name"]))
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(doc)


_JOB_ORDER = ["name", "needs", "if", "runs-on", "environment", "concurrency", "permissions",
              "container", "services", "strategy", "env", "defaults", "timeout-minutes",
              "continue-on-error", "steps"]

# `uses`/`run` must lead a step; `with` reads as gibberish before the action it configures.
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


MIGRATION = AzurePipelinesToGha()
