"""variables — job-level variables."""

from portover.core import MappingMeta

SCOPE = "job"

META = MappingMeta(
    id="job-variables",
    directive="<job>.variables",
    title="Migrate GitLab CI job variables to GitHub Actions",
    before="""deploy:
  variables:
    APP_ENV: production
    DEPLOY_KEY: $PROD_DEPLOY_KEY""",
    after="""deploy:
  env:
    APP_ENV: production
    DEPLOY_KEY: ${{ secrets.PROD_DEPLOY_KEY }}""",
    notes=(
        "Job variables become the job's `env:` and override the workflow-level "
        "block, same precedence as GitLab. A value that just forwards another "
        "variable (`$PROD_DEPLOY_KEY`) is almost always a masked CI/CD variable "
        "from the GitLab UI — portover rewrites those references to "
        "`${{ secrets.NAME }}` and flags them so you remember to create the "
        "secret."
    ),
    priority=16,
)


def matches(key) -> bool:
    return key == "variables"


def apply(key, value, job, ctx, report) -> None:
    if not isinstance(value, dict):
        return
    for name, spec in value.items():
        text = str(spec) if spec is not None else ""
        if text.startswith("$") and text[1:].replace("{", "").replace("}", "").isidentifier():
            secret = text.strip("${}")
            job.setdefault("env", {})[name] = "${{ secrets.%s }}" % secret
            report.manual(META.id, f"{name}: {text}",
                          f"looks like a masked CI/CD variable — create repository secret {secret}")
        else:
            job.setdefault("env", {})[name] = spec
            report.mapped(META.id, f"variables.{name}")
