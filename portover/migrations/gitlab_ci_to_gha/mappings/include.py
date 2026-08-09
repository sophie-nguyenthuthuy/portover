"""include — pulling in other config files."""

from portover.core import MappingMeta

SCOPE = "pipeline"

META = MappingMeta(
    id="include",
    directive="include: local / project / remote / template",
    title="Migrate GitLab CI include to GitHub Actions",
    before="""include:
  - local: /ci/tests.yml
  - template: Security/SAST.gitlab-ci.yml
  - project: my-group/ci-templates
    file: /deploy.yml""",
    after="""# no include chain — the closest equivalents are:
#   local   -> paste the jobs in, or make it a reusable workflow (workflow_call)
#   project -> a reusable workflow in another repo:
#              uses: my-org/ci-templates/.github/workflows/deploy.yml@main
#   template-> find the marketplace action (SAST -> github/codeql-action)""",
    notes=(
        "portover only reads the file you point it at, so jobs defined in an "
        "include are NOT in the output — run portover against each included file "
        "too, or inline them first. GitLab's `template:` includes are GitLab-"
        "authored pipelines (SAST, Dependency Scanning, Code Quality); their GHA "
        "counterparts are marketplace actions or GitHub-native features like "
        "CodeQL and Dependabot, not a line-by-line translation."
    ),
    manual=True,
    priority=16,
)

_HINTS = {
    "local": "paste those jobs into this config, or extract a reusable workflow (on: workflow_call)",
    "project": "cross-repo reuse: `uses: <owner>/<repo>/.github/workflows/<file>@<ref>`",
    "remote": "no remote include — vendor the file into the repo",
    "template": "GitLab-authored template — use the GitHub-native equivalent (e.g. SAST -> github/codeql-action)",
    "component": "CI/CD component — the nearest GHA unit is a reusable workflow or a composite action",
}


def matches(key) -> bool:
    return key == "include"


def apply(key, value, ctx, report) -> None:
    from portover.migrations.gitlab_ci_to_gha import as_list

    for entry in as_list(value):
        if isinstance(entry, str):
            report.manual(META.id, f"include: {entry}", _HINTS["local"])
            continue
        if not isinstance(entry, dict):
            continue
        for kind, target in entry.items():
            if kind in ("file", "ref", "inputs"):
                continue
            report.manual(META.id, f"include.{kind}: {target}",
                          _HINTS.get(kind, "no GHA equivalent — inline the jobs it defines"))
