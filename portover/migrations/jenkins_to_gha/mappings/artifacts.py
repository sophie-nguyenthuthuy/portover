"""junit / archiveArtifacts / stash / unstash."""

from portover.core import MappingMeta
from portover.migrations.jenkins_to_gha.parser import call_arg, kwargs

SCOPE = "step"

META = MappingMeta(
    id="artifacts",
    directive="archiveArtifacts / junit / stash / unstash",
    title="Migrate Jenkins artifact steps to GitHub Actions",
    before="archiveArtifacts artifacts: 'dist/**'\njunit 'reports/**/*.xml'",
    after="""- uses: actions/upload-artifact@v4
  with: { name: dist, path: dist/** }
- uses: actions/upload-artifact@v4
  if: always()
  with: { name: test-reports, path: reports/**/*.xml }""",
    notes=(
        "junit has no built-in equivalent — reports are uploaded as artifacts; "
        "add a marketplace reporter (e.g. dorny/test-reporter) for annotations. "
        "stash/unstash between stages becomes upload-artifact in one job and "
        "download-artifact in the job that needs: it."
    ),
    priority=14,
)


def matches(stmt: str) -> bool:
    return stmt.split("(")[0].split()[0] in ("archiveArtifacts", "junit", "stash", "unstash")


def apply(stmt: str, steps: list, ctx, report) -> None:
    kind = stmt.split("(")[0].split()[0]
    kw = kwargs(stmt)
    if kind == "archiveArtifacts":
        path = kw.get("artifacts") or call_arg(stmt)
        steps.append({"uses": "actions/upload-artifact@v4", "with": {"name": "artifacts", "path": path}})
        report.mapped(META.id, stmt, f"upload-artifact: {path}")
    elif kind == "junit":
        path = kw.get("testResults") or call_arg(stmt)
        steps.append({"uses": "actions/upload-artifact@v4", "if": "always()",
                      "with": {"name": "test-reports", "path": path}})
        report.manual(META.id, stmt, "junit reports uploaded as artifact — add dorny/test-reporter for PR annotations")
    elif kind == "stash":
        name = kw.get("name") or "stash"
        steps.append({"uses": "actions/upload-artifact@v4", "with": {"name": name, "path": kw.get("includes", "**")}})
        report.mapped(META.id, stmt, f"upload-artifact '{name}'")
    else:  # unstash
        name = call_arg(stmt) or kwargs(stmt).get("name", "stash")
        steps.append({"uses": "actions/download-artifact@v4", "with": {"name": name}})
        report.mapped(META.id, stmt, f"download-artifact '{name}'")
