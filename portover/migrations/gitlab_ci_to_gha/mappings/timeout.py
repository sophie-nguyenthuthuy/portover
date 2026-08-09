"""timeout — job time limit."""

from portover.core import MappingMeta

SCOPE = "job"

META = MappingMeta(
    id="timeout",
    directive="timeout: 1h 30m",
    title="Migrate GitLab CI timeout to GitHub Actions",
    before="timeout: 1h 30m",
    after="timeout-minutes: 90",
    notes=(
        "GitLab accepts human durations ('3 hours 30 minutes'); GHA takes "
        "whole minutes. Note the defaults differ sharply — GitLab defaults to "
        "1 hour per job, GHA to 6 hours — so a job that relied on GitLab's "
        "default to kill a hang will now run six times longer. If a timeout "
        "mattered, set it explicitly."
    ),
    priority=38,
)


def matches(key) -> bool:
    return key == "timeout"


def apply(key, value, job, ctx, report) -> None:
    from portover.migrations.gitlab_ci_to_gha import minutes

    total = minutes(value)
    if total is None:
        report.manual(META.id, f"timeout: {value}", "could not parse the duration — set timeout-minutes by hand")
        return
    job["timeout-minutes"] = total
    report.mapped(META.id, f"timeout: {value}", f"timeout-minutes: {total}")
