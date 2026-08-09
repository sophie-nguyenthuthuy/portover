"""machine — CircleCI VM executor."""

from portover.core import MappingMeta

SCOPE = "job"

META = MappingMeta(
    id="machine", directive="machine: {image: ...}",
    title="Migrate a CircleCI machine executor",
    before="""machine:
  image: ubuntu-2204:current""",
    after="runs-on: ubuntu-22.04",
    notes="CircleCI and GitHub runner images are not identical; validate installed tools after migration.",
    priority=10,
)


def matches(key) -> bool:
    return key == "machine"


def apply(key, value, job, ctx, report) -> None:
    image = value.get("image", "") if isinstance(value, dict) else value
    s = str(image)
    if "2204" in s or "22.04" in s:
        job["runs-on"] = "ubuntu-22.04"
    elif "2404" in s or "24.04" in s:
        job["runs-on"] = "ubuntu-24.04"
    else:
        job["runs-on"] = "ubuntu-latest"
        if image not in (True, None, ""):
            report.manual(META.id, f"machine image: {image}", "verify the closest GitHub-hosted runner image")
    report.mapped(META.id, f"machine: {image}", f"runs-on: {job['runs-on']}")
