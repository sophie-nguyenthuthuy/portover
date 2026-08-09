"""env / timeout / soft_fail / retry / concurrency / priority — the remaining step fields."""

from portover.core import MappingMeta

SCOPE = "step"

META = MappingMeta(
    id="step-settings",
    directive="env / timeout_in_minutes / soft_fail / retry / concurrency / priority",
    title="Migrate the remaining Buildkite step settings to GitHub Actions",
    before="""env:
  DEPLOY_ENV: production
timeout_in_minutes: 30
soft_fail: true
concurrency: 1
concurrency_group: deploy
retry:
  automatic:
    limit: 2""",
    after="""env:
  DEPLOY_ENV: production
timeout-minutes: 30
continue-on-error: true       # soft_fail
concurrency:
  group: deploy
  cancel-in-progress: false""",
    notes=(
        "Most are renames. Two are not: `soft_fail` with an `exit_status` list "
        "(tolerate only certain codes) has no equivalent — `continue-on-error` "
        "tolerates any failure — so handle specific codes in the command. And "
        "`retry.automatic` has no counterpart at job level; GHA offers "
        "re-running a failed job by hand, or wrapping the flaky command in a "
        "retry action, and neither can filter on Buildkite's exit-status "
        "conditions. `retry.manual` is simply the re-run button, which GHA has "
        "built in."
    ),
    priority=24,
)


def matches(key) -> bool:
    return key in ("env", "timeout_in_minutes", "soft_fail", "retry", "concurrency",
                   "concurrency_group", "priority", "cancel_on_build_failing",
                   "allow_dependency_failure", "notify", "id", "identifier")


def apply(key, value, job, ctx, report) -> None:
    from portover.migrations.buildkite_to_gha import as_list, interpolate, note_vars

    if key == "env":
        if isinstance(value, dict):
            for name, spec in value.items():
                note_vars(spec, ctx)
                job.setdefault("env", {})[str(name)] = interpolate(spec, ctx)
            report.mapped(META.id, f"env: {len(value)} variable(s)")
        return
    if key == "timeout_in_minutes":
        try:
            job["timeout-minutes"] = int(value)
            report.mapped(META.id, f"timeout_in_minutes: {value}", "timeout-minutes")
        except (TypeError, ValueError):
            report.manual(META.id, f"timeout_in_minutes: {value}", "could not parse — set timeout-minutes by hand")
        return
    if key == "soft_fail":
        if isinstance(value, list):
            codes = [str(e.get("exit_status")) for e in value if isinstance(e, dict)]
            job["continue-on-error"] = True
            report.manual(META.id, f"soft_fail exit_status: {codes}",
                          "continue-on-error tolerates ANY failure — handle those specific exit "
                          "codes in the command (e.g. `cmd || [ $? -eq 2 ]`)")
        elif value:
            job["continue-on-error"] = True
            report.mapped(META.id, "soft_fail: true", "continue-on-error: true")
        return
    if key == "retry":
        automatic = value.get("automatic") if isinstance(value, dict) else value
        if automatic:
            limit = automatic.get("limit") if isinstance(automatic, dict) else 2
            report.manual(META.id, f"retry.automatic: {automatic}",
                          f"no job-level retry in GHA — wrap the flaky command in nick-fields/retry "
                          f"(max_attempts: {int(limit or 2) + 1}); Buildkite's exit_status filter "
                          "cannot be expressed")
        if isinstance(value, dict) and value.get("manual") is not None:
            report.mapped(META.id, "retry.manual", "GHA has a built-in re-run button")
        return
    if key in ("concurrency", "concurrency_group"):
        group = str(value) if key == "concurrency_group" else None
        existing = job.get("concurrency") or {}
        if group:
            existing["group"] = group
        existing.setdefault("cancel-in-progress", False)
        job["concurrency"] = existing
        if key == "concurrency" and not isinstance(value, str):
            report.mapped(META.id, f"concurrency: {value}",
                          "GHA concurrency is a group, not a count — 1 is serialised, "
                          "higher limits have no equivalent")
        else:
            report.mapped(META.id, f"{key}: {value}", "job concurrency group")
        return
    if key == "cancel_on_build_failing":
        report.manual(META.id, f"cancel_on_build_failing: {value}",
                      "no equivalent — GHA cancels remaining jobs only via concurrency or fail-fast")
        return
    if key == "priority":
        report.mapped(META.id, f"priority: {value}", "dropped — GHA has no queue priority")
        return
    if key == "notify":
        report.manual(META.id, "step notify",
                      "per-step notifications — add a notifying step with `if: failure()`")
        return
    if key in ("id", "identifier"):
        report.mapped(META.id, f"{key}: {value}", "the job id already carries this")
