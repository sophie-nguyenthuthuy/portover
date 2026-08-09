"""trigger — CI triggers."""

from portover.core import MappingMeta

SCOPE = "pipeline"

META = MappingMeta(
    id="trigger",
    directive="trigger: branches / tags / paths / none",
    title="Migrate Azure Pipelines trigger to GitHub Actions on push",
    before="""trigger:
  branches:
    include: [main, release/*]
    exclude: [experimental/*]
  paths:
    include: [src/*]
  tags:
    include: ["v*"]""",
    after="""on:
  push:
    branches: [main, "release/*"]
    branches-ignore: [experimental/*]
    paths: [src/*]
    tags: ["v*"]""",
    notes=(
        "include/exclude become branches/branches-ignore, and Azure's `*` "
        "wildcards are already GHA glob syntax. Two gotchas: `trigger: none` "
        "means no CI trigger at all (portover drops `on: push` rather than "
        "leaving a trigger that would fire unexpectedly), and the bare list "
        "form `trigger: [main]` is branch-only shorthand. Note GHA cannot put "
        "branches and branches-ignore on the same event — if your config uses "
        "both, portover keeps includes and flags the excludes."
    ),
    priority=10,
)


def matches(key) -> bool:
    return key == "trigger"


def apply(key, value, ctx, report) -> None:
    from portover.migrations.azure_pipelines_to_gha import as_list

    if value is None or str(value).lower() == "none":
        ctx.on.setdefault("pull_request", {})
        report.mapped(META.id, "trigger: none", "no push trigger emitted")
        return
    push: dict = {}
    if isinstance(value, list):
        push["branches"] = [str(b) for b in value]
        report.mapped(META.id, f"trigger: {push['branches']}", "on.push.branches")
    elif isinstance(value, dict):
        if value.get("batch") is not None:
            report.manual(META.id, f"trigger.batch: {value['batch']}",
                          "no batching in GHA — the closest is a concurrency group with cancel-in-progress")
        for section, (inc_key, exc_key) in (("branches", ("branches", "branches-ignore")),
                                            ("paths", ("paths", "paths-ignore")),
                                            ("tags", ("tags", "tags-ignore"))):
            spec = value.get(section)
            if spec is None:
                continue
            includes = [str(v) for v in as_list(spec.get("include") if isinstance(spec, dict) else spec)]
            excludes = [str(v) for v in as_list(spec.get("exclude") if isinstance(spec, dict) else None)]
            if includes:
                push[inc_key] = includes
                report.mapped(META.id, f"trigger.{section}.include", f"on.push.{inc_key}")
            if excludes:
                if includes:
                    report.manual(META.id, f"trigger.{section}.exclude: {excludes}",
                                  f"GHA cannot combine {inc_key} with {exc_key} on one event — "
                                  "fold the exclusion into the include globs")
                else:
                    push[exc_key] = excludes
                    report.mapped(META.id, f"trigger.{section}.exclude", f"on.push.{exc_key}")
    if push or isinstance(value, dict):
        ctx.on["push"] = push
