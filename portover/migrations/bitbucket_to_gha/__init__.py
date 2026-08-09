"""bitbucket-pipelines.yml (Bitbucket Pipelines) -> GitHub Actions workflows.

The mapping that shapes everything else: **a Bitbucket step is a GitHub Actions
job, not a step.** Each Bitbucket step runs in its own container, gets its own
fresh clone, and only receives files from earlier steps through declared
artifacts — which is exactly what a GHA job is. So a step's `script:` list
becomes that job's `run:` steps, and the sequential order of steps becomes a
`needs:` chain (a `parallel:` block is where that chain fans out).

The other structural point: one file holds several independently triggered
pipelines (default, branches, tags, pull-requests, custom). GHA scopes triggers
per file, so each one becomes its own workflow file.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from portover.core import Migration, Report, load_mappings
from portover.emit import yaml_dump
from portover.miniyaml import MiniYamlError, parse

CONFIG_PATHS = ("bitbucket-pipelines.yml", "bitbucket-pipelines.yaml")

_VAR = re.compile(r"\$\{?(BITBUCKET_[A-Z0-9_]+|CI)\}?")


@dataclass
class BitbucketContext:
    default_image: object = None
    clone: dict = field(default_factory=dict)
    options: dict = field(default_factory=dict)
    caches: dict = field(default_factory=dict)  # custom cache name -> path
    services: dict = field(default_factory=dict)  # service name -> definition
    used_vars: set = field(default_factory=set)
    current_jid: str = ""


def slug(name: str) -> str:
    s = re.sub(r"[^a-z0-9_-]+", "-", str(name).lower()).strip("-")
    if not s:
        return "step"
    return s if s[0].isalpha() or s[0] == "_" else f"step-{s}"


def as_list(value):
    if value is None:
        return []
    return list(value) if isinstance(value, list) else [value]


def scoped(scope: str) -> list:
    return [m for m in load_mappings(BitbucketToGha.package)
            if getattr(m, "SCOPE", "pipeline") == scope]


def note_vars(text, ctx) -> None:
    """Record which BITBUCKET_* variables a script actually uses."""
    if isinstance(text, str):
        ctx.used_vars.update(_VAR.findall(text))


def build_step(definition: dict, ctx: BitbucketContext, report: Report,
               *, index: int, taken: set) -> tuple:
    """Convert one Bitbucket step definition into a GHA job. Returns (jid, job)."""
    name = str(definition.get("name") or f"step {index}")
    jid = slug(name)
    while jid in taken:
        jid = f"{jid}-{index}"
    taken.add(jid)

    job: dict = {"runs-on": "ubuntu-latest"}
    if slug(name) != name:
        job["name"] = name
    ctx.current_jid = jid

    if ctx.default_image is not None and "image" not in definition:
        _apply_field("image", ctx.default_image, job, ctx, report)
    if ctx.clone and "clone" not in definition:
        _apply_field("clone", ctx.clone, job, ctx, report)
    if ctx.options.get("max-time") and "max-time" not in definition:
        job["timeout-minutes"] = int(ctx.options["max-time"])

    for field_name, spec in definition.items():
        if field_name == "name":
            continue
        _apply_field(field_name, spec, job, ctx, report)

    steps: list = [] if job.pop("_no_checkout", False) else [_checkout(job)]
    steps.extend(job.pop("_pre_steps", []))
    steps.extend(job.pop("_script", []))
    steps.extend(job.pop("_post_steps", []))
    steps.extend(job.pop("_after_script", []))
    job["steps"] = steps
    if not any("run" in s for s in steps):
        report.manual("script", name, "step has no script — add its commands by hand")
    return jid, job


def _apply_field(field_name, spec, job, ctx, report) -> None:
    for m in scoped("step"):
        if m.matches(field_name):
            m.apply(field_name, spec, job, ctx, report)
            return
    report.unmapped.append(f"step field: {field_name}")


def _checkout(job: dict) -> dict:
    checkout: dict = {"uses": "actions/checkout@v4"}
    with_ = job.pop("_checkout_with", None)
    if with_:
        checkout["with"] = with_
    return checkout


class BitbucketToGha(Migration):
    id = "bitbucket-to-gha"
    source = "bitbucket-pipelines.yml (Bitbucket Pipelines)"
    target = ".github/workflows/*.yml (GitHub Actions)"
    package = "portover.migrations.bitbucket_to_gha"

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
                          "Bitbucket configs lean on anchors under `definitions:`; expand them and retry")
            return report
        if not isinstance(doc, dict):
            report.manual("parse", found[0], "expected a top-level mapping")
            return report

        ctx = BitbucketContext()
        keys = list(doc)
        for m in scoped("pipeline"):
            for key in [k for k in keys if m.matches(k)]:
                m.apply(key, doc[key], ctx, report)
                keys.remove(key)
        for key in keys:
            report.unmapped.append(f"{found[0]}: {key}")

        if not report.outputs:
            report.manual("pipelines", found[0], "no `pipelines:` block — nothing to convert")
        return report


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


MIGRATION = BitbucketToGha()
