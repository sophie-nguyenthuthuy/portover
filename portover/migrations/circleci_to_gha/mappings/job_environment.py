"""environment — job environment variables."""

from portover.core import MappingMeta

SCOPE = "job"

META = MappingMeta(
    id="job-environment", directive="jobs.<job>.environment",
    title="Migrate CircleCI job environment variables",
    before="""environment:
  APP_ENV: test""",
    after="""env:
  APP_ENV: test""",
    notes="Do not migrate secret values into YAML; replace them with `${{ secrets.NAME }}`.",
    priority=20,
)


def matches(key) -> bool:
    return key == "environment"


def apply(key, value, job, ctx, report) -> None:
    if isinstance(value, dict):
        job.setdefault("env", {}).update(value)
        report.mapped(META.id, "job environment", f"{len(value)} variable(s)")
