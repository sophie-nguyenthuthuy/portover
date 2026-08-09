"""executors — reusable executor definitions."""

from portover.core import MappingMeta

SCOPE = "pipeline"

META = MappingMeta(
    id="executors",
    directive="executors: (reusable executors)",
    title="Migrate CircleCI reusable executors to GitHub Actions",
    before="""executors:
  py:
    docker:
      - image: cimg/python:3.12

jobs:
  test:
    executor: py""",
    after="""jobs:
  test:
    runs-on: ubuntu-latest
    container: cimg/python:3.12""",
    notes=(
        "GHA has no named-executor concept, so portover resolves the reference "
        "and writes the runner/container inline in every job that used it. If "
        "several jobs share one executor and you want to keep that DRY, a "
        "reusable workflow (workflow_call) is the closest equivalent."
    ),
    priority=16,
)


def matches(key) -> bool:
    return key == "executors"


def apply(key, value, ctx, report) -> None:
    if not isinstance(value, dict):
        return
    for name, definition in value.items():
        ctx.executors[name] = definition if isinstance(definition, dict) else {}
        report.mapped(META.id, f"executors.{name}", "resolved inline where referenced")
