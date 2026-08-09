"""allow_failure — a job that may fail without failing the pipeline."""

from portover.core import MappingMeta

SCOPE = "job"

META = MappingMeta(
    id="allow-failure",
    directive="allow_failure: true / {exit_codes}",
    title="Migrate GitLab CI allow_failure to GitHub Actions",
    before="allow_failure: true",
    after="continue-on-error: true",
    notes=(
        "A direct translation. The visible difference is reporting: GitLab "
        "shows the job as 'passed with warnings' (orange), while GHA marks the "
        "run green and you have to open the job to see the failure. "
        "`allow_failure: {exit_codes: [137]}` — tolerate only specific exit "
        "codes — has no equivalent; handle it in the script with a trap or an "
        "explicit `|| exit 0` for the codes you accept."
    ),
    priority=36,
)


def matches(key) -> bool:
    return key == "allow_failure"


def apply(key, value, job, ctx, report) -> None:
    if isinstance(value, dict):
        report.manual(META.id, f"allow_failure: {value}",
                      "per-exit-code tolerance has no equivalent — handle those codes in the script")
        job["continue-on-error"] = True
        return
    job["continue-on-error"] = bool(value)
    report.mapped(META.id, f"allow_failure: {value}", f"continue-on-error: {bool(value)}")
