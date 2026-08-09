"""working_directory — apply a default directory to run steps."""

from portover.core import MappingMeta

SCOPE = "job"

META = MappingMeta(
    id="working-directory", directive="working_directory: path",
    title="Migrate a CircleCI job working directory",
    before="working_directory: ~/project/subdir",
    after="""defaults:
  run:
    working-directory: subdir""",
    notes="GHA paths are relative to the checked-out workspace; `~/project/` is removed.",
    priority=20,
)


def matches(key) -> bool:
    return key == "working_directory"


def apply(key, value, job, ctx, report) -> None:
    path = str(value).removeprefix("~/project/")
    if path == "~/project":
        path = "."
    job.setdefault("defaults", {}).setdefault("run", {})["working-directory"] = path
    report.mapped(META.id, f"working_directory: {value}", f"defaults.run.working-directory: {path}")
