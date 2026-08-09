"""condition — job run conditions."""

from portover.core import MappingMeta
from portover.migrations.azure_pipelines_to_gha.expr import translate

SCOPE = "job"

META = MappingMeta(
    id="condition",
    directive="condition: and(succeeded(), eq(...))",
    title="Migrate Azure Pipelines conditions to GitHub Actions if",
    before="condition: and(succeeded(), eq(variables['Build.SourceBranch'], 'refs/heads/main'))",
    after="if: success() && github.ref == 'refs/heads/main'",
    notes=(
        "Azure conditions are prefix functions, GHA expressions are infix, so "
        "portover parses the condition properly rather than pattern-matching "
        "it. Status checks translate directly: succeeded() -> success(), "
        "failed() -> failure(), always() -> always(), succeededOrFailed() -> "
        "always(). Watch the implicit default — an Azure job without a "
        "condition implicitly means succeeded(), while a GHA job with no `if:` "
        "also only runs when its needs succeeded, so the two agree. But adding "
        "ANY `if:` to a GHA job does NOT drop that implicit success check; "
        "`always()` is what overrides it, exactly as in Azure."
    ),
    priority=22,
)


def matches(key) -> bool:
    return key == "condition"


def apply(key, value, job, ctx, report) -> None:
    condition = translate(value, report, META.id)
    if not condition:
        return
    job["if"] = f"{job['if']} && {condition}" if job.get("if") else condition
    report.mapped(META.id, f"condition: {value}", condition)
