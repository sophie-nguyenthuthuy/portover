"""CI_* predefined variables used inside scripts."""

from portover.core import MappingMeta

SCOPE = "transform"  # not a config key: a post-pass over the scripts

META = MappingMeta(
    id="ci-variables",
    directive="$CI_COMMIT_SHA, $CI_COMMIT_BRANCH, $CI_REGISTRY_IMAGE, ...",
    title="Migrate GitLab CI predefined variables to GitHub Actions",
    before="""script:
  - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .
  - echo "built from $CI_COMMIT_BRANCH\"""",
    after="""env:   # added automatically, so the scripts keep working unchanged
  CI: "true"
  CI_REGISTRY_IMAGE: ghcr.io/${{ github.repository }}
  CI_COMMIT_SHA: ${{ github.sha }}
  CI_COMMIT_BRANCH: ${{ github.ref_name }}""",
    notes=(
        "Rather than rewriting every shell command (and risking a bad edit "
        "inside a quoted string), portover defines the GitLab variables your "
        "scripts actually use as workflow-level `env:` sourced from the github "
        "context. The scripts stay byte-for-byte identical and keep working. "
        "Only variables that are genuinely referenced get defined. A few have "
        "no faithful equivalent and are flagged instead: CI_COMMIT_SHORT_SHA "
        "(GHA expressions cannot truncate — use "
        "`$(git rev-parse --short HEAD)`), CI_JOB_TOKEN (GITHUB_TOKEN is scoped "
        "differently and cannot clone other private repos), and CI_PIPELINE_URL."
    ),
    priority=95,
)

# GitLab variable -> GHA expression
COMPAT = {
    "CI": '"true"',
    "CI_COMMIT_SHA": "${{ github.sha }}",
    "CI_COMMIT_REF_NAME": "${{ github.ref_name }}",
    "CI_COMMIT_BRANCH": "${{ github.ref_name }}",
    "CI_COMMIT_REF_SLUG": "${{ github.ref_name }}",
    "CI_COMMIT_TAG": "${{ github.ref_type == 'tag' && github.ref_name || '' }}",
    "CI_COMMIT_MESSAGE": "${{ github.event.head_commit.message }}",
    "CI_DEFAULT_BRANCH": "${{ github.event.repository.default_branch }}",
    "CI_PROJECT_DIR": "${{ github.workspace }}",
    "CI_PROJECT_NAME": "${{ github.event.repository.name }}",
    "CI_PROJECT_PATH": "${{ github.repository }}",
    "CI_PROJECT_URL": "${{ github.server_url }}/${{ github.repository }}",
    "CI_PIPELINE_ID": "${{ github.run_id }}",
    "CI_PIPELINE_IID": "${{ github.run_number }}",
    "CI_PIPELINE_SOURCE": "${{ github.event_name }}",
    "CI_JOB_ID": "${{ github.run_id }}",
    "CI_JOB_NAME": "${{ github.job }}",
    "CI_RUNNER_TAGS": "${{ runner.os }}",
    "CI_SERVER_URL": "${{ github.server_url }}",
    "CI_API_V4_URL": "${{ github.api_url }}",
    "CI_REGISTRY": "ghcr.io",
    "CI_REGISTRY_IMAGE": "ghcr.io/${{ github.repository }}",
    "CI_REGISTRY_USER": "${{ github.actor }}",
    "CI_MERGE_REQUEST_IID": "${{ github.event.pull_request.number }}",
    "CI_MERGE_REQUEST_TARGET_BRANCH_NAME": "${{ github.base_ref }}",
    "CI_MERGE_REQUEST_SOURCE_BRANCH_NAME": "${{ github.head_ref }}",
}

NO_EQUIVALENT = {
    "CI_COMMIT_SHORT_SHA": "GHA expressions cannot truncate — use `$(git rev-parse --short HEAD)` in the script",
    "CI_JOB_TOKEN": "use `${{ secrets.GITHUB_TOKEN }}`, but note it cannot clone other private repos like CI_JOB_TOKEN can",
    "CI_PIPELINE_URL": "build it: ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}",
    "CI_REGISTRY_PASSWORD": "use `${{ secrets.GITHUB_TOKEN }}` when logging in to ghcr.io",
    "GITLAB_CI": "the GHA equivalent flag is GITHUB_ACTIONS",
    "CI_NODE_INDEX": "set by the parallel mapping from the job matrix",
    "CI_NODE_TOTAL": "set by the parallel mapping from the job matrix",
}


def matches(key) -> bool:
    return False  # dispatched by the driver, not by a config key


def compat_env(ctx, report) -> dict:
    """Define the GitLab variables the scripts actually reference."""
    env = {}
    for name in sorted(ctx.used_ci_vars):
        if name in COMPAT:
            env[name] = COMPAT[name]
            report.mapped(META.id, f"${name}", f"env.{name} = {COMPAT[name]}")
        elif name in NO_EQUIVALENT:
            report.manual(META.id, f"${name}", NO_EQUIVALENT[name])
        else:
            report.manual(META.id, f"${name}", "no GHA equivalent — define it yourself or drop the reference")
    return env
