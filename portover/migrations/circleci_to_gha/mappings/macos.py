"""macos — CircleCI macOS executor."""

from portover.core import MappingMeta

SCOPE = "job"

META = MappingMeta(
    id="macos", directive="macos: {xcode: ...}",
    title="Migrate a CircleCI macOS executor",
    before="""macos:
  xcode: 15.4.0""",
    after="runs-on: macos-14",
    notes="Xcode is selected through the runner image on GHA; verify the current runner/Xcode table.",
    priority=10,
)


def matches(key) -> bool:
    return key == "macos"


def apply(key, value, job, ctx, report) -> None:
    job["runs-on"] = "macos-14"
    xcode = value.get("xcode") if isinstance(value, dict) else None
    report.manual(META.id, f"macos xcode: {xcode}",
                  "verify macos-14 contains the required Xcode version")
