"""sh / bat / powershell steps."""

from portover.core import MappingMeta
from portover.migrations.jenkins_to_gha.parser import call_arg, kwargs

SCOPE = "step"

META = MappingMeta(
    id="sh",
    directive="sh 'cmd' / bat 'cmd'",
    title="Migrate Jenkins sh and bat steps to GitHub Actions run",
    before="sh 'make test'",
    after="- run: make test",
    notes=(
        "sh -> run (bash). bat -> run with shell: cmd — and the job must be on "
        "a windows-latest runner. sh(returnStdout: true) captured into a Groovy "
        "variable becomes `>> \"$GITHUB_OUTPUT\"` plumbing (flagged)."
    ),
    priority=10,
)


def matches(stmt: str) -> bool:
    return stmt.split("(")[0].split()[0] in ("sh", "bat", "powershell") if stmt.strip() else False


def apply(stmt: str, steps: list, ctx, report) -> None:
    kind = stmt.split("(")[0].split()[0]
    kw = kwargs(stmt)
    script = kw.get("script") or call_arg(stmt)
    step: dict = {"run": script}
    if kind == "bat":
        step["shell"] = "cmd"
        report.manual(META.id, stmt, "bat step: set the job's runs-on to windows-latest")
    elif kind == "powershell":
        step["shell"] = "pwsh"
    if kw.get("returnStdout") or kw.get("returnStatus"):
        report.manual(META.id, stmt, 'captured output: write it to "$GITHUB_OUTPUT" and read via steps.<id>.outputs')
    steps.append(step)
    if kind == "sh":
        report.mapped(META.id, stmt)
