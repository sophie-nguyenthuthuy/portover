"""schedules — cron triggers."""

from portover.core import MappingMeta

SCOPE = "pipeline"

META = MappingMeta(
    id="schedules",
    directive="schedules: [{cron, branches, always}]",
    title="Migrate Azure Pipelines schedules to GitHub Actions",
    before="""schedules:
  - cron: "0 3 * * *"
    displayName: Nightly
    branches:
      include: [main]
    always: true""",
    after="""on:
  schedule:
    - cron: "0 3 * * *\"""",
    notes=(
        "The cron syntax is identical (both UTC, both 5-field). What does not "
        "carry over is the branch filter: an Azure schedule names the branches "
        "to build, while a GHA scheduled run ALWAYS uses the default branch — "
        "there is no way to schedule a different branch, so a schedule for a "
        "non-default branch needs rethinking. `always: false` (skip when there "
        "are no new commits) also has no equivalent; GHA runs the schedule "
        "regardless."
    ),
    priority=14,
)


def matches(key) -> bool:
    return key == "schedules"


def apply(key, value, ctx, report) -> None:
    from portover.migrations.azure_pipelines_to_gha import as_list

    for entry in as_list(value):
        if not isinstance(entry, dict) or not entry.get("cron"):
            continue
        cron = str(entry["cron"]).strip()
        ctx.on.setdefault("schedule", []).append({"cron": cron})
        report.mapped(META.id, f"schedules.cron: {cron}", "on.schedule")
        branches = entry.get("branches")
        if isinstance(branches, dict) and branches.get("include"):
            names = [str(b) for b in as_list(branches["include"])]
            if names not in (["main"], ["master"]):
                report.manual(META.id, f"schedules.branches: {names}",
                              "GHA scheduled runs always use the default branch — "
                              "a schedule for another branch cannot be expressed")
        if entry.get("always") is False:
            report.manual(META.id, "schedules.always: false",
                          "GHA runs schedules even with no new commits — add a guard step if that matters")
