"""group — a named collection of steps."""

from portover.core import MappingMeta

SCOPE = "structure"

META = MappingMeta(
    id="group",
    directive="- group: name / steps / depends_on",
    title="Migrate Buildkite group steps to GitHub Actions",
    before="""- group: ":test: Tests"
  key: tests
  depends_on: build
  steps:
    - label: Unit
      command: make unit
    - label: Lint
      command: make lint""",
    after="""jobs:
  unit:
    needs: build      # the group's depends_on, applied to each member
    steps: [...]
  lint:
    needs: build
    steps: [...]""",
    notes=(
        "A group is presentation plus a shared dependency — GHA has no "
        "grouping construct, so portover flattens it and pushes the group's "
        "`depends_on` onto each member. The part that does not survive is the "
        "group KEY: other steps can `depends_on` a whole group in Buildkite, "
        "but a GHA job cannot depend on a set, so portover expands such a "
        "reference into every job the group contained."
    ),
    priority=44,
)


def matches(key) -> bool:
    return key == "group"


def expand(entry: dict, ctx, report) -> None:
    from portover.migrations.buildkite_to_gha import as_list, slug
    from portover.migrations.buildkite_to_gha.mappings import depends_on as depends_map
    from portover.migrations.buildkite_to_gha.mappings import steps as steps_map

    label = str(entry.get("group") or entry.get("label") or "group")
    group_needs = depends_map.resolve(entry.get("depends_on"), ctx, report) if entry.get("depends_on") else []
    before = len(ctx.job_order)
    steps_map.walk(entry.get("steps"), ctx, report, group_needs=group_needs)
    members = ctx.job_order[before:]
    if entry.get("key"):
        # a group key stands for every job inside it
        ctx.keys[str(entry["key"])] = members
    report.mapped(META.id, f"group: {label}", f"flattened into {len(members)} job(s)")
    if entry.get("if") or entry.get("branches"):
        report.manual(META.id, f"group: {label} condition",
                      "a group-level condition applies to every member — copy the `if:` onto each job")
