"""pool — which agent runs the work."""

from portover.core import MappingMeta

SCOPE = "pipeline"

META = MappingMeta(
    id="pool",
    directive="pool: vmImage / name / demands",
    title="Migrate Azure Pipelines pool to GitHub Actions runs-on",
    before="""pool:
  vmImage: ubuntu-latest""",
    after="runs-on: ubuntu-latest",
    notes=(
        "Microsoft-hosted `vmImage` values map almost one-to-one, including the "
        "older names (ubuntu-20.04, windows-2019, macOS-latest -> "
        "macos-latest). A `name:` pool instead of a vmImage means a self-hosted "
        "agent pool, which becomes a self-hosted runner label; `demands:` "
        "(capability matching) has no GHA equivalent beyond adding more labels. "
        "A top-level pool applies to every job unless the job sets its own."
    ),
    priority=16,
)

_IMAGES = {
    "ubuntu-latest": "ubuntu-latest", "ubuntu-22.04": "ubuntu-22.04", "ubuntu-20.04": "ubuntu-20.04",
    "ubuntu-24.04": "ubuntu-24.04", "windows-latest": "windows-latest", "windows-2022": "windows-2022",
    "windows-2019": "windows-2019", "vs2017-win2016": "windows-2019",
    "macos-latest": "macos-latest", "macos-13": "macos-13", "macos-12": "macos-12",
    "macos-11": "macos-13", "ubuntu-18.04": "ubuntu-22.04", "ubuntu-16.04": "ubuntu-22.04",
}


def matches(key) -> bool:
    return key == "pool"


def apply(key, value, ctx, report) -> None:
    ctx.default_pool = value if isinstance(value, dict) else {"vmImage": value}
    report.mapped(META.id, "pool (pipeline)", "applied to every job that has no pool of its own")


def resolve(value, job, ctx, report) -> None:
    """Set runs-on from a pool spec (used for both pipeline and job pools)."""
    spec = value if isinstance(value, dict) else {"vmImage": value}
    image = spec.get("vmImage") or spec.get("vmimage")
    if image:
        key = str(image).lower()
        runner = _IMAGES.get(key)
        if runner is None:
            runner = "ubuntu-latest"
            report.manual(META.id, f"pool.vmImage: {image}",
                          f"unknown or retired image — defaulted to {runner}; pick the closest GitHub-hosted runner")
        else:
            if key != runner:
                report.manual(META.id, f"pool.vmImage: {image}",
                              f"that image is retired on GHA — mapped to {runner}")
            else:
                report.mapped(META.id, f"pool.vmImage: {image}", f"runs-on: {runner}")
        job["runs-on"] = runner
    elif spec.get("name"):
        labels = ["self-hosted", str(spec["name"])]
        job["runs-on"] = labels
        report.manual(META.id, f"pool.name: {spec['name']}",
                      "a self-hosted agent pool — register the machines as GitHub self-hosted runners with this label")
    if spec.get("demands"):
        report.manual(META.id, f"pool.demands: {spec['demands']}",
                      "no capability matching in GHA — encode the requirement as runner labels")
