"""trigger — downstream / child pipelines."""

from portover.core import MappingMeta

SCOPE = "job"

META = MappingMeta(
    id="trigger",
    directive="trigger: project / include / strategy",
    title="Migrate GitLab CI trigger to GitHub Actions",
    before="""deploy-downstream:
  trigger:
    project: my-group/deployer
    branch: main
    strategy: depend""",
    after="""deploy-downstream:
  uses: my-org/deployer/.github/workflows/deploy.yml@main
  secrets: inherit""",
    notes=(
        "A multi-project trigger becomes a reusable workflow call — note the "
        "job then uses `uses:` INSTEAD of `runs-on`/`steps`, and the called "
        "workflow must declare `on: workflow_call`. `strategy: depend` (wait "
        "for the downstream result) is the default for a called workflow, so "
        "that comes for free. A child-pipeline trigger (`trigger: include:`) "
        "has no real equivalent: put those jobs in the same workflow, or split "
        "them into a reusable workflow too. If you need to fire and forget "
        "across repos, that is `repository_dispatch` plus a token."
    ),
    manual=True,
    priority=48,
)


def matches(key) -> bool:
    return key == "trigger"


def apply(key, value, job, ctx, report) -> None:
    if isinstance(value, dict):
        project = value.get("project")
        if value.get("include"):
            report.manual(META.id, "trigger.include (child pipeline)",
                          "no child pipelines — inline those jobs here or extract a reusable workflow")
            return
        branch = value.get("branch", "main")
        target = f"{project} @{branch}" if project else "downstream pipeline"
    else:
        target = str(value)
    report.manual(META.id, f"trigger: {target}",
                  "replace this job with a reusable-workflow call: "
                  "`uses: <owner>/<repo>/.github/workflows/<file>@<ref>` (plus `secrets: inherit`), "
                  "and add `on: workflow_call` to the called workflow")
