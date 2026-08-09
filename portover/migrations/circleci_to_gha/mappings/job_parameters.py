"""parameters — job parameters are supplied by a workflow matrix."""

from portover.core import MappingMeta

SCOPE = "job"

META = MappingMeta(
    id="job-parameters", directive="jobs.<job>.parameters",
    title="Migrate CircleCI job parameters",
    before="""parameters:
  python:
    type: string""",
    after="""strategy:
  matrix:
    python: [\"3.11\", \"3.12\"]""",
    notes=(
        "The CircleCI workflow call site supplies matrix parameter values. "
        "References inside commands become `${{ matrix.<name> }}`. A job used "
        "without a matrix may need its defaults written directly into the workflow."
    ),
    priority=20,
)


def matches(key) -> bool:
    return key == "parameters"


def apply(key, value, job, ctx, report) -> None:
    names = sorted(value) if isinstance(value, dict) else []
    report.mapped(META.id, "job parameters", f"matrix references: {names}")
