"""retry — automatic re-run on failure."""

from portover.core import MappingMeta

SCOPE = "job"

META = MappingMeta(
    id="retry",
    directive="retry: 2 / retry: {max, when}",
    title="Migrate GitLab CI retry to GitHub Actions",
    before="""retry:
  max: 2
  when: runner_system_failure""",
    after="""# no built-in job retry; per-step:
- uses: nick-fields/retry@v3
  with:
    max_attempts: 3
    command: pytest -q""",
    notes=(
        "GHA has no job-level automatic retry — the built-in options are "
        "re-running a failed job by hand from the UI, or wrapping the flaky "
        "command in a retry action. GitLab's `when:` filter (retry only on "
        "runner_system_failure, script_failure, job_execution_timeout...) has "
        "no counterpart either: a retry action retries on any non-zero exit. "
        "Retrying only infrastructure failures is not expressible, so treat "
        "this as a behaviour change, not a translation."
    ),
    manual=True,
    priority=40,
)


def matches(key) -> bool:
    return key == "retry"


def apply(key, value, job, ctx, report) -> None:
    if isinstance(value, dict):
        attempts = value.get("max", 1)
        condition = value.get("when")
        detail = f"wrap the flaky command in nick-fields/retry with max_attempts: {int(attempts) + 1}"
        if condition:
            detail += f" — note `when: {condition}` cannot be expressed; it will retry on any failure"
    else:
        detail = f"wrap the flaky command in nick-fields/retry with max_attempts: {int(value) + 1}"
    report.manual(META.id, f"retry: {value}", detail)
