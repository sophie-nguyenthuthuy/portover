"""environment — deployment target."""

from portover.core import MappingMeta

SCOPE = "job"

META = MappingMeta(
    id="environment",
    directive="environment: name / url / on_stop",
    title="Migrate GitLab CI environment to GitHub Actions",
    before="""environment:
  name: production
  url: https://example.com""",
    after="""environment:
  name: production
  url: https://example.com""",
    notes=(
        "Nearly identical — both track deployments per named environment and "
        "both show the URL. GHA environments additionally carry protection "
        "rules (required reviewers, wait timers, branch restrictions) and "
        "environment-scoped secrets, which is where GitLab's `when: manual` "
        "deploy gate ends up. `on_stop`/`auto_stop_in` (GitLab's dynamic "
        "environment teardown) have no equivalent: write an explicit cleanup "
        "job. Dynamic names like `review/$CI_COMMIT_REF_NAME` work, but the "
        "variable must be a GHA expression."
    ),
    priority=42,
)


def matches(key) -> bool:
    return key == "environment"


def apply(key, value, job, ctx, report) -> None:
    from portover.migrations.gitlab_ci_to_gha import note_ci_vars

    if not isinstance(value, dict):
        job["environment"] = str(value)
        report.mapped(META.id, f"environment: {value}")
        return
    spec: dict = {}
    if value.get("name") is not None:
        spec["name"] = str(value["name"])
        note_ci_vars(spec["name"], ctx)
    if value.get("url") is not None:
        spec["url"] = str(value["url"])
        note_ci_vars(spec["url"], ctx)
    for unsupported in ("on_stop", "auto_stop_in", "action", "kubernetes"):
        if unsupported in value:
            report.manual(META.id, f"environment.{unsupported}",
                          "no equivalent — write an explicit cleanup job for teardown")
    if spec:
        job["environment"] = spec if len(spec) > 1 else spec.get("name", "")
        report.mapped(META.id, f"environment.name: {spec.get('name')}")
