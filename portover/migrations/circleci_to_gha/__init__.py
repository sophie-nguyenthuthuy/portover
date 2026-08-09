""".circleci/config.yml (CircleCI) -> GitHub Actions workflows.

The structural difference that shapes this whole migration: in CircleCI a
`job` is a *definition* and a `workflow` *instantiates* it (with requires,
filters, matrix, context). In GitHub Actions a job is both at once. So:

- the `jobs:` mapping converts each definition into a GHA job dict, held in
  ctx.job_defs but not yet emitted;
- the `workflows:` mapping emits one workflow FILE per CircleCI workflow,
  copying in the job defs it references and applying requires -> needs and
  filters -> if.

A config with no `workflows:` key (CircleCI 2.0) falls back to emitting every
job definition into a single ci.yml.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from portover.core import Migration, Report, load_mappings
from portover.emit import yaml_dump
from portover.miniyaml import MiniYamlError, parse

CONFIG_PATHS = (".circleci/config.yml", ".circleci/config.yaml")

_PIPELINE_PARAM = re.compile(r"<<\s*pipeline\.parameters\.([A-Za-z0-9_-]+)\s*>>")
_JOB_PARAM = re.compile(r"<<\s*parameters\.([A-Za-z0-9_-]+)\s*>>")


@dataclass
class CircleContext:
    workflow_name: str = "CI"
    commands: dict = field(default_factory=dict)  # name -> command definition
    executors: dict = field(default_factory=dict)  # name -> executor definition
    job_defs: dict = field(default_factory=dict)  # slug -> GHA job dict
    job_raw: dict = field(default_factory=dict)  # slug -> CircleCI job definition
    job_names: dict = field(default_factory=dict)  # original name -> slug
    inputs: dict = field(default_factory=dict)  # workflow_dispatch inputs
    orbs: dict = field(default_factory=dict)  # alias -> orb reference
    command_args: list[dict] = field(default_factory=list)  # nested reusable-command arguments


def slug(name: str) -> str:
    s = re.sub(r"[^a-z0-9_-]+", "-", str(name).lower()).strip("-")
    if not s:
        return "job"
    return s if s[0].isalpha() or s[0] == "_" else f"job-{s}"


def interpolate(value, ctx=None):
    """Rewrite CircleCI parameter tokens into GHA expressions."""
    if not isinstance(value, str):
        return value
    value = _PIPELINE_PARAM.sub(r"${{ inputs.\1 }}", value)
    def job_param(match):
        name = match.group(1)
        if ctx and ctx.command_args and name in ctx.command_args[-1]:
            return str(ctx.command_args[-1][name])
        return "${{ matrix." + name + " }}"
    return _JOB_PARAM.sub(job_param, value)


def scoped(package: str, scope: str) -> list:
    return [m for m in load_mappings(package) if getattr(m, "SCOPE", "pipeline") == scope]


def step_name(item):
    """A CircleCI step is either a bare string or a single-key mapping."""
    if isinstance(item, str):
        return item, None
    if isinstance(item, dict) and len(item) == 1:
        (name, value), = item.items()
        return name, value
    return None, item


def convert_steps(items, ctx: CircleContext, report: Report, *, depth: int = 0) -> list:
    """Convert a CircleCI steps list into GHA steps."""
    from portover.migrations.circleci_to_gha.mappings import commands as commands_map

    out: list = []
    maps = scoped(CircleCiToGha.package, "step")
    for item in items or []:
        name, value = step_name(item)
        if name is None:
            report.unmapped.append(f"step: {item!r}")
            continue
        if name in ctx.commands:  # user-defined reusable command
            out.extend(commands_map.inline(name, value, ctx, report, depth=depth))
            continue
        for m in maps:
            if m.matches(name):
                m.apply(name, value, out, ctx, report)
                break
        else:
            report.unmapped.append(f"step: {name}")
    return out


class CircleCiToGha(Migration):
    id = "circleci-to-gha"
    source = ".circleci/config.yml (CircleCI)"
    target = ".github/workflows/*.yml (GitHub Actions)"
    package = "portover.migrations.circleci_to_gha"

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
                          "expand anchors/aliases (CircleCI's `circleci config process` does this) and retry")
            return report
        if not isinstance(doc, dict):
            report.manual("parse", found[0], "expected a top-level mapping")
            return report

        ctx = CircleContext()
        keys = list(doc)
        for m in scoped(self.package, "pipeline"):
            for key in [k for k in keys if m.matches(k)]:
                m.apply(key, doc[key], ctx, report)
                keys.remove(key)
        for key in keys:
            report.unmapped.append(f"{found[0]}: {key}")

        if not report.outputs and ctx.job_defs:  # no workflows: block (CircleCI 2.0)
            from portover.migrations.circleci_to_gha.mappings.workflows import order_job

            workflow = {"name": "CI", "on": self.default_on(),
                        "jobs": {jid: order_job(job) for jid, job in ctx.job_defs.items()}}
            if ctx.inputs:
                workflow["on"]["workflow_dispatch"] = {"inputs": ctx.inputs}
            report.outputs[".github/workflows/ci.yml"] = yaml_dump(workflow) + "\n"
            report.manual("workflows", "workflows",
                          "no `workflows:` block — jobs were emitted unordered; add needs: if they must run in sequence")
        elif not ctx.job_defs:
            report.manual("jobs", "jobs", "no job definitions found to convert")
        return report

    @staticmethod
    def default_on() -> dict:
        # CircleCI runs branch pipelines without a main-only restriction.
        return {"push": {}, "pull_request": {}}


MIGRATION = CircleCiToGha()
