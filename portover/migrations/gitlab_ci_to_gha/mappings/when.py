"""when — job-level run condition."""

from portover.core import MappingMeta

SCOPE = "job"

META = MappingMeta(
    id="when",
    directive="when: manual / always / on_failure / delayed",
    title="Migrate GitLab CI when to GitHub Actions",
    before="""cleanup:
  when: always

deploy:
  when: manual""",
    after="""cleanup:
  if: always()

deploy:
  # gated by an environment with required reviewers,
  # or triggered from on: workflow_dispatch""",
    notes=(
        "`always` and `on_failure` are `if: always()` and `if: failure()`. "
        "`manual` is the interesting one: GitLab puts a play button on the job "
        "inside an otherwise-automatic pipeline, which GHA has no per-job "
        "equivalent for. The two honest options are an environment with "
        "required reviewers (the job runs but waits for approval) or a separate "
        "workflow_dispatch trigger. `delayed` with `start_in:` has no "
        "equivalent at all — the closest is a sleep step or a scheduled "
        "workflow."
    ),
    priority=34,
)

_CONDITIONS = {"always": "always()", "on_failure": "failure()", "on_success": None}


def matches(key) -> bool:
    return key == "when"


def apply(key, value, job, ctx, report) -> None:
    mode = str(value)
    if mode in _CONDITIONS:
        condition = _CONDITIONS[mode]
        if condition:
            job["if"] = f"{job['if']} && {condition}" if job.get("if") else condition
            report.mapped(META.id, f"when: {mode}", f"if: {condition}")
        else:
            report.mapped(META.id, "when: on_success", "the GHA default — no condition needed")
        return
    if mode == "manual":
        job["environment"] = job.get("environment") or "manual-approval"
        report.manual(META.id, "when: manual",
                      "no per-job play button — this job now points at an Environment "
                      "('manual-approval'); add required reviewers to it, or trigger the job via workflow_dispatch")
        return
    if mode == "delayed":
        report.manual(META.id, "when: delayed",
                      "no delayed start — use a `sleep` step or move the job to a scheduled workflow")
        return
    if mode == "never":
        report.manual(META.id, "when: never", "job never runs — delete it, or gate it with `if: false`")
        return
    report.manual(META.id, f"when: {mode}", "unrecognized when: value")
