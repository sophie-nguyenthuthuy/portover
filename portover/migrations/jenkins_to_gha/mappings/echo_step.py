"""echo steps."""

from portover.core import MappingMeta
from portover.migrations.jenkins_to_gha.parser import call_arg

SCOPE = "step"

META = MappingMeta(
    id="echo",
    directive="echo 'message'",
    title="Migrate Jenkins echo steps to GitHub Actions",
    before="echo 'Deploying to staging'",
    after='- run: echo "Deploying to staging"',
    notes="Groovy ${VAR} interpolation inside the message must become ${{ env.VAR }} or shell $VAR.",
    priority=12,
)


def matches(stmt: str) -> bool:
    return stmt.startswith(("echo ", "echo("))


def apply(stmt: str, steps: list, ctx, report) -> None:
    msg = call_arg(stmt).replace('"', '\\"')
    steps.append({"run": f'echo "{msg}"'})
    report.mapped(META.id, stmt)
