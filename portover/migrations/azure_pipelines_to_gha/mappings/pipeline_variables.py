"""variables — the pipeline-level block (job-level lives in job_variables)."""

from portover.core import MappingMeta
from portover.migrations.azure_pipelines_to_gha.mappings import job_variables

SCOPE = "pipeline"

META = MappingMeta(
    id="pipeline-variables",
    directive="variables: (pipeline level)",
    title="Migrate Azure Pipelines pipeline-level variables to GitHub Actions",
    before="""variables:
  buildConfiguration: Release
  vmImageName: ubuntu-latest""",
    after="""env:
  buildConfiguration: Release
  vmImageName: ubuntu-latest""",
    notes=(
        "Pipeline variables become workflow-level `env:`, visible to every job "
        "— the same scope Azure gives them. They are also what lets portover "
        "tell an Azure `$(macro)` apart from bash command substitution: a name "
        "declared here is rewritten in scripts, anything else is left alone. "
        "See the variables page for the group/template forms."
    ),
    priority=19,
)


def matches(key) -> bool:
    return key == "variables"


def apply(key, value, ctx, report) -> None:
    job_variables.apply_pipeline(value, ctx, report)
