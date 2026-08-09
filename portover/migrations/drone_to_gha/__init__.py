""".drone.yml (Drone CI) -> GitHub Actions workflow.

Drone's model differs from every other CI here in one important way: its steps
run in separate containers but SHARE the workspace volume, so files written by
one step are simply there for the next. That is GHA's *step* semantics, not its
job semantics — files persist across steps of a job and vanish between jobs. So:

    one Drone pipeline  ->  one GHA job
    one Drone step      ->  one GHA step

which keeps the shared workspace intact for free. The wrinkle is that each
Drone step names its own `image:` while GHA containers are per JOB. When every
step shares one image the job simply gets `container:`; when they differ, each
step runs `docker run` against its own image with the workspace bind-mounted,
which preserves both the images and the shared files.

A .drone.yml is also a multi-document stream — several pipelines separated by
`---`, wired together with pipeline-level `depends_on` — so those become
several jobs in one workflow.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from portover.core import Migration, Report, load_mappings
from portover.emit import yaml_dump
from portover.miniyaml import MiniYamlError, parse_all

CONFIG_PATHS = (".drone.yml", ".drone.yaml")

WORKSPACE = "/drone/src"

_VAR = re.compile(r"\$\{?(DRONE_[A-Z0-9_]+|CI)\}?")


@dataclass
class DroneContext:
    jobs: dict = field(default_factory=dict)
    job_order: list = field(default_factory=list)
    names: dict = field(default_factory=dict)  # pipeline name -> job id
    depends: dict = field(default_factory=dict)  # job id -> [pipeline name]
    on: dict = field(default_factory=dict)
    used_vars: set = field(default_factory=set)
    current_jid: str = ""
    secrets: set = field(default_factory=set)
    trigger_variants: list = field(default_factory=list)
    plain_push: bool = False  # a push event was asked for, not only tags
    # per-step scratch, set by the steps mapping before each step's fields run
    step_image: str = ""
    step_shared_image: bool = True
    step_env: dict = field(default_factory=dict)


def slug(name: str) -> str:
    s = re.sub(r"[^a-z0-9_-]+", "-", str(name).lower()).strip("-")
    s = re.sub(r"-{2,}", "-", s)
    if not s:
        return "pipeline"
    return s if s[0].isalpha() or s[0] == "_" else f"job-{s}"


def as_list(value):
    if value is None:
        return []
    return list(value) if isinstance(value, list) else [value]


def scoped(scope: str) -> list:
    return [m for m in load_mappings(DroneToGha.package)
            if getattr(m, "SCOPE", "pipeline") == scope]


def note_vars(text, ctx) -> None:
    if isinstance(text, str):
        ctx.used_vars.update(_VAR.findall(text))


def secret_ref(value, ctx, report, *, source: str = ""):
    """`{from_secret: name}` -> ${{ secrets.NAME }}."""
    if isinstance(value, dict) and "from_secret" in value:
        name = re.sub(r"[^A-Za-z0-9_]", "_", str(value["from_secret"])).upper()
        ctx.secrets.add(name)
        return "${{ secrets.%s }}" % name
    return value


class DroneToGha(Migration):
    id = "drone-to-gha"
    source = ".drone.yml (Drone CI)"
    target = ".github/workflows/*.yml (GitHub Actions)"
    package = "portover.migrations.drone_to_gha"

    def detect(self, root) -> list[str]:
        root = Path(root)
        return [p for p in CONFIG_PATHS if (root / p).exists()]

    def run(self, root) -> Report:
        root = Path(root)
        report = Report(self.id)
        found = self.detect(root)
        try:
            documents = parse_all((root / found[0]).read_text())
        except MiniYamlError as e:
            report.manual("parse", found[0],
                          f"config uses YAML features portover's reader skips ({e}) — "
                          "expand anchors/aliases and retry")
            return report

        ctx = DroneContext()
        for document in documents:
            if not isinstance(document, dict) or not document:
                continue
            self.convert_document(document, ctx, report, source=found[0])

        if not ctx.jobs:
            report.manual("pipeline", found[0], "no docker/exec pipelines found to convert")
            return report

        self.wire(ctx, report)
        report.outputs[".github/workflows/ci.yml"] = yaml_dump(self.assemble(ctx, report)) + "\n"
        return report

    def convert_document(self, document: dict, ctx: DroneContext, report: Report, *, source: str) -> None:
        from portover.migrations.drone_to_gha.mappings import kind as kind_map

        if not kind_map.is_pipeline(document, ctx, report):
            return
        name = str(document.get("name") or "default")
        jid = slug(name)
        while jid in ctx.jobs:
            jid = f"{jid}-{len(ctx.job_order)}"
        ctx.names[name] = jid
        ctx.current_jid = jid

        job: dict = {"runs-on": "ubuntu-latest"}
        if slug(name) != name:
            job["name"] = name
        ctx.depends[jid] = [str(d) for d in as_list(document.get("depends_on"))]

        pipeline_maps = scoped("pipeline")
        for field_name, spec in document.items():
            if field_name in ("kind", "name", "depends_on"):
                continue
            for m in pipeline_maps:
                if m.matches(field_name):
                    m.apply(field_name, spec, job, ctx, report)
                    break
            else:
                report.unmapped.append(f"{source} ({name}): {field_name}")

        steps: list = [] if job.pop("_no_checkout", False) else [_checkout(job)]
        steps.extend(job.pop("_steps", []))
        job["steps"] = steps
        if not steps:
            report.manual("steps", name, "pipeline has no steps — add its commands by hand")
        ctx.jobs[jid] = job
        ctx.job_order.append(jid)
        report.mapped("pipeline", f"pipeline: {name}", f"job '{jid}' ({len(steps)} steps)")

    def wire(self, ctx: DroneContext, report: Report) -> None:
        for jid, parents in ctx.depends.items():
            needs = [ctx.names.get(p, slug(p)) for p in parents]
            needs = [n for n in needs if n in ctx.jobs and n != jid]
            if needs:
                ctx.jobs[jid]["needs"] = needs if len(needs) > 1 else needs[0]
                report.mapped("pipeline-depends", f"{jid} depends_on {parents}", f"needs: {needs}")

    def assemble(self, ctx: DroneContext, report: Report) -> dict:
        from portover.migrations.drone_to_gha.mappings import variables as variables_map

        _fix_push_filters(ctx)
        workflow: dict = {"name": "CI", "on": ctx.on or {"push": {}, "pull_request": {}}}
        env = variables_map.compat_env(ctx, report)
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


MIGRATION = DroneToGha()
