"""variables — global pipeline variables."""

from portover.core import MappingMeta

SCOPE = "pipeline"

META = MappingMeta(
    id="variables",
    directive="variables: (global)",
    title="Migrate GitLab CI global variables to GitHub Actions env",
    before="""variables:
  APP_ENV: production
  PIP_CACHE_DIR: .cache/pip
  DEPLOY_TOKEN:
    description: set at pipeline run time""",
    after="""env:
  APP_ENV: production
  PIP_CACHE_DIR: .cache/pip""",
    notes=(
        "Plain values map to a workflow-level `env:` block. Two things do not "
        "carry over: masked/protected CI/CD variables set in the GitLab UI have "
        "no YAML representation at all — recreate them as repository secrets and "
        "reference `${{ secrets.NAME }}`; and a variable declared with a "
        "`description:` is a run-time input in GitLab, which is a "
        "workflow_dispatch input in GHA."
    ),
    priority=12,
)


def matches(key) -> bool:
    return key == "variables"


def apply(key, value, ctx, report) -> None:
    if not isinstance(value, dict):
        return
    for name, spec in value.items():
        if isinstance(spec, dict):
            if "value" in spec:
                ctx.variables[name] = spec["value"]
            report.manual(META.id, f"variables.{name}",
                          "declared with description/options — this is a run-time input; "
                          "add it under `on: workflow_dispatch: inputs:`")
            continue
        ctx.variables[name] = spec
        report.mapped(META.id, f"variables.{name}")
