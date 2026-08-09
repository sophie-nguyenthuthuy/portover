"""checkout scm / deleteDir / cleanWs housekeeping steps."""

from portover.core import MappingMeta

SCOPE = "step"

META = MappingMeta(
    id="checkout",
    directive="checkout scm",
    title="Migrate Jenkins checkout scm to GitHub Actions",
    before="checkout scm",
    after="- uses: actions/checkout@v4",
    notes=(
        "portover already prepends actions/checkout to every job (declarative "
        "pipelines check out implicitly), so an explicit `checkout scm` is "
        "dropped rather than duplicated. deleteDir/cleanWs are no-ops: every "
        "GHA job starts on a fresh workspace."
    ),
    priority=8,
)


def matches(stmt: str) -> bool:
    return stmt.startswith("checkout") or stmt.split("(")[0] in ("deleteDir", "cleanWs")


def apply(stmt: str, steps: list, ctx, report) -> None:
    if stmt.startswith("checkout"):
        report.mapped(META.id, stmt, "dropped — checkout is already the first step of every job")
    else:
        report.mapped(META.id, stmt, "dropped — GHA jobs always start on a fresh workspace")
