"""resource_class — CircleCI runner sizing."""

from portover.core import MappingMeta

SCOPE = "job"

META = MappingMeta(
    id="resource-class", directive="resource_class: medium", title="Migrate CircleCI resource classes",
    before="resource_class: large", after="runs-on: ubuntu-latest  # select a larger runner in repository settings",
    notes=(
        "Runner sizes and billing tiers do not map one-to-one. Standard CircleCI classes stay on the generated "
        "runner; select a GHA larger-runner label or self-hosted label if the job needs more capacity."
    ),
    manual=True, priority=30,
)


def matches(key) -> bool:
    return key == "resource_class"


def apply(key, value, job, ctx, report) -> None:
    report.manual(META.id, f"resource_class: {value}",
                  f"verify `{job.get('runs-on', 'ubuntu-latest')}` has enough CPU and memory")
