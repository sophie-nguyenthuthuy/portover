"""trigger — which events start the pipeline."""

from portover.core import MappingMeta

SCOPE = "pipeline"

META = MappingMeta(
    id="trigger",
    directive="trigger: branch / event / ref / cron",
    title="Migrate Drone trigger to GitHub Actions",
    before="""trigger:
  branch:
    - main
  event:
    - push
    - tag""",
    after="""on:
  push:
    branches: [main]
    tags: ["*"]

jobs:
  default:
    if: github.ref_name == 'main'   # kept per job, see below""",
    notes=(
        "A Drone trigger is per PIPELINE, while GHA triggers are per WORKFLOW "
        "file — and one .drone.yml can hold several pipelines with different "
        "triggers. portover therefore does both: it widens the workflow's `on:` "
        "to cover every pipeline's events, and keeps each pipeline's own "
        "conditions as an `if:` on its job. That combination fires the same "
        "runs Drone would. `event: tag` adds `on: push: tags:` — without a tag "
        "trigger the job's `if:` could never fire. `cron:` names a Drone-side "
        "schedule that is not in this file, so it is flagged."
    ),
    priority=14,
)

_EVENT_TRIGGERS = {
    "push": ("push", {}),
    "pull_request": ("pull_request", {}),
    "tag": ("push", {"tags": ["*"]}),
    "cron": ("schedule", None),
    "custom": ("workflow_dispatch", {}),
    "promote": ("workflow_dispatch", {}),
    "rollback": ("workflow_dispatch", {}),
}


def matches(key) -> bool:
    return key == "trigger"


def apply(key, value, job, ctx, report) -> None:
    from portover.migrations.drone_to_gha import as_list
    from portover.migrations.drone_to_gha.mappings import when as when_map

    if not isinstance(value, dict):
        return

    events = [str(e) for e in as_list(value.get("event", {}).get("include")
                                      if isinstance(value.get("event"), dict) else value.get("event"))]
    for event in events:
        entry = _EVENT_TRIGGERS.get(event)
        if entry is None:
            report.manual(META.id, f"trigger.event: {event}", "unrecognised Drone event")
            continue
        name, spec = entry
        if spec is None:
            report.manual(META.id, "trigger.event: cron",
                          "the schedule itself lives in Drone's UI, not this file — add "
                          "`on: schedule: - cron: ...` with the right expression")
            continue
        if event == "push":
            ctx.plain_push = True
        existing = ctx.on.setdefault(name, {})
        for k, v in spec.items():
            existing.setdefault(k, v)
        report.mapped(META.id, f"trigger.event: {event}", f"on.{name}")

    branches = value.get("branch")
    if branches is not None and "push" in ctx.on:
        names = [str(b) for b in as_list(branches.get("include")
                                         if isinstance(branches, dict) else branches)]
        if names:
            ctx.on["push"].setdefault("branches", [])
            for name in names:
                if name not in ctx.on["push"]["branches"]:
                    ctx.on["push"]["branches"].append(name)
            report.mapped(META.id, f"trigger.branch: {names}", "on.push.branches")

    condition = when_map.build(value, ctx, report)
    if condition:
        job["if"] = f"{job['if']} && {condition}" if job.get("if") else condition
        report.mapped(META.id, "trigger (per-pipeline)", f"job if: {condition}")
