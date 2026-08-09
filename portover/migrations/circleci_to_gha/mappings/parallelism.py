"""parallelism — fan a job out with a matrix."""

from portover.core import MappingMeta

SCOPE = "job"

META = MappingMeta(
    id="parallelism", directive="parallelism: N", title="Migrate CircleCI job parallelism",
    before="parallelism: 4", after="""strategy:
  matrix:
    circle_node_index: [0, 1, 2, 3]
env:
  CIRCLE_NODE_INDEX: ${{ matrix.circle_node_index }}""",
    notes="The fan-out is preserved, but CircleCI timing-based test splitting must be replaced with a test-runner sharding feature.",
    manual=True, priority=30,
)


def matches(key) -> bool:
    return key == "parallelism"


def apply(key, value, job, ctx, report) -> None:
    try:
        count = int(value)
    except (TypeError, ValueError):
        report.manual(META.id, f"parallelism: {value}", "set a matrix with one entry per parallel node")
        return
    job.setdefault("strategy", {}).setdefault("matrix", {})["circle_node_index"] = list(range(count))
    job.setdefault("env", {})["CIRCLE_NODE_INDEX"] = "${{ matrix.circle_node_index }}"
    job["env"]["CIRCLE_NODE_TOTAL"] = count
    report.manual(META.id, f"parallelism: {count}",
                  "matrix fan-out added; replace `circleci tests split` with your test runner's sharding option")
