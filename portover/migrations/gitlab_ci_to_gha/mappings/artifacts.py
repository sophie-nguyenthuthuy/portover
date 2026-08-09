"""artifacts — files kept after the job, and test reports."""

from portover.core import MappingMeta

SCOPE = "job"

META = MappingMeta(
    id="artifacts",
    directive="artifacts: paths / reports / expire_in / when",
    title="Migrate GitLab CI artifacts to GitHub Actions",
    before="""artifacts:
  paths:
    - dist/
  reports:
    junit: report.xml
  expire_in: 1 week
  when: always""",
    after="""- uses: actions/upload-artifact@v4
  if: always()
  with:
    name: dist
    path: dist/
    retention-days: 7""",
    notes=(
        "`paths` becomes upload-artifact and `expire_in` becomes "
        "retention-days. The real difference is `reports:` — GitLab parses "
        "those files and renders test results, coverage and security findings "
        "in the MR. GHA has no built-in report parsing: junit needs a reporter "
        "action (dorny/test-reporter), coverage needs a coverage action or a "
        "third-party service, and the security reports map to GitHub Advanced "
        "Security features rather than a file upload. portover uploads them as "
        "plain artifacts so nothing is lost, and flags each one."
    ),
    priority=26,
)

_REPORT_HINTS = {
    "junit": "add dorny/test-reporter to annotate the PR with test results",
    "coverage_report": "use a coverage action (e.g. irongut/CodeCoverageSummary) or Codecov",
    "cobertura": "use a coverage action (e.g. irongut/CodeCoverageSummary) or Codecov",
    "sast": "GitHub's equivalent is code scanning — github/codeql-action",
    "dependency_scanning": "GitHub's equivalent is Dependabot / dependency review",
    "secret_detection": "GitHub's equivalent is secret scanning (repo setting)",
    "codequality": "use a linter action that emits SARIF and upload it with github/codeql-action/upload-sarif",
}


def matches(key) -> bool:
    return key == "artifacts"


def _days(expire_in) -> int | None:
    from portover.migrations.gitlab_ci_to_gha import minutes

    text = str(expire_in).strip().lower()
    if text in ("never", "0"):
        return None
    total = minutes(text)
    if total is None:
        return None
    if "week" in text:
        total = float(str(text).split()[0] or 1) * 7 * 1440
    elif "month" in text:
        total = float(str(text).split()[0] or 1) * 30 * 1440
    elif "year" in text:
        total = float(str(text).split()[0] or 1) * 365 * 1440
    return max(1, min(90, int(round(total / 1440)))) or 1


def apply(key, value, job, ctx, report) -> None:
    from portover.migrations.gitlab_ci_to_gha import as_list

    if not isinstance(value, dict):
        return
    paths = [str(p) for p in as_list(value.get("paths"))]
    reports = value.get("reports") if isinstance(value.get("reports"), dict) else {}
    for kind, target in (reports or {}).items():
        paths.extend(str(t) for t in as_list(target))
        report.manual(META.id, f"artifacts.reports.{kind}",
                      _REPORT_HINTS.get(kind, "GHA has no report parsing — uploaded as a plain artifact"))
    if not paths:
        if value.get("expose_as"):
            report.manual(META.id, "artifacts.expose_as", "no MR-attachment equivalent — artifacts appear on the run page")
        return

    step: dict = {"uses": "actions/upload-artifact@v4"}
    when = str(value.get("when", "on_success"))
    if when in ("always", "on_failure"):
        step["if"] = "always()" if when == "always" else "failure()"
        report.mapped(META.id, f"artifacts.when: {when}", step["if"])
    with_: dict = {"name": str(value.get("name") or ctx.current_jid or "artifacts"),
                   "path": "\n".join(paths) if len(paths) > 1 else paths[0]}
    if value.get("expire_in") is not None:
        days = _days(value["expire_in"])
        if days:
            with_["retention-days"] = days
            report.mapped(META.id, f"artifacts.expire_in: {value['expire_in']}", f"retention-days: {days}")
        else:
            report.manual(META.id, f"artifacts.expire_in: {value['expire_in']}",
                          "GHA caps retention at 90 days — 'never' is not available")
    step["with"] = with_
    job.setdefault("_post_steps", []).append(step)
    report.mapped(META.id, f"artifacts.paths: {paths}", "upload-artifact")
