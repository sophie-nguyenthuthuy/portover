"""$CI_* variables used in commands."""

from portover.core import MappingMeta

SCOPE = "transform"

META = MappingMeta(
    id="ci-variables",
    directive="$CI_COMMIT_SHA, $CI_COMMIT_BRANCH, $CI_PIPELINE_NUMBER, ...",
    title="Migrate Woodpecker CI_ variables to GitHub Actions",
    before="""commands:
  - docker build -t app:$CI_COMMIT_SHA .
  - echo "branch $CI_COMMIT_BRANCH pipeline $CI_PIPELINE_NUMBER\"""",
    after="""env:   # added automatically, so the commands keep working unchanged
  CI_COMMIT_SHA: ${{ github.sha }}
  CI_COMMIT_BRANCH: ${{ github.ref_name }}
  CI_PIPELINE_NUMBER: ${{ github.run_number }}""",
    notes=(
        "Woodpecker uses the CI_ prefix where Drone used DRONE_ (2.0 dropped "
        "the DRONE_ aliases entirely), and they are plain shell variables — so "
        "portover defines the ones your commands reference as workflow-level "
        "`env:` from the github context and leaves the commands untouched. "
        "Note CI_ is a broad prefix: a variable that is not a Woodpecker "
        "built-in is reported rather than invented, since it is probably one "
        "of your own and needs defining. CI_WORKSPACE points at "
        "/woodpecker/src rather than the GHA workspace, and CI_PREV_* "
        "(previous build) has no counterpart at all."
    ),
    priority=95,
)

COMPAT = {
    "CI": '"true"',
    "CI_COMMIT_SHA": "${{ github.sha }}",
    "CI_COMMIT_BRANCH": "${{ github.ref_name }}",
    "CI_COMMIT_REF": "${{ github.ref }}",
    "CI_COMMIT_TAG": "${{ github.ref_type == 'tag' && github.ref_name || '' }}",
    "CI_COMMIT_MESSAGE": "${{ github.event.head_commit.message }}",
    "CI_COMMIT_AUTHOR": "${{ github.actor }}",
    "CI_COMMIT_AUTHOR_EMAIL": "${{ github.actor }}",
    "CI_COMMIT_SOURCE_BRANCH": "${{ github.head_ref }}",
    "CI_COMMIT_TARGET_BRANCH": "${{ github.base_ref }}",
    "CI_COMMIT_PULL_REQUEST": "${{ github.event.pull_request.number }}",
    "CI_PIPELINE_NUMBER": "${{ github.run_number }}",
    "CI_PIPELINE_EVENT": "${{ github.event_name }}",
    "CI_PIPELINE_URL": "${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}",
    "CI_PIPELINE_FORGE_URL": "${{ github.server_url }}/${{ github.repository }}",
    "CI_REPO": "${{ github.repository }}",
    "CI_REPO_NAME": "${{ github.event.repository.name }}",
    "CI_REPO_OWNER": "${{ github.repository_owner }}",
    "CI_REPO_URL": "${{ github.server_url }}/${{ github.repository }}",
    "CI_REPO_CLONE_URL": "${{ github.server_url }}/${{ github.repository }}.git",
    "CI_REPO_DEFAULT_BRANCH": "${{ github.event.repository.default_branch }}",
    "CI_STEP_NAME": "${{ github.job }}",
    "CI_WORKFLOW_NAME": "${{ github.workflow }}",
    "CI_FORGE_URL": "${{ github.server_url }}",
    "CI_SYSTEM_NAME": '"github-actions"',
}

NO_EQUIVALENT = {
    "CI_WORKSPACE": "use ${{ github.workspace }} — there is no /woodpecker/src on a GHA runner",
    "CI_COMMIT_SHA_SHORT": "GHA expressions cannot truncate — use `$(git rev-parse --short HEAD)`",
    "CI_PIPELINE_STATUS": "branch on ${{ job.status }}, or use if: success() / if: failure() steps",
    "CI_STEP_STATUS": "branch on ${{ job.status }} instead",
    "CI_PIPELINE_STARTED": "no start timestamp — capture one with `date +%s` if you need it",
    "CI_PIPELINE_FINISHED": "no finish timestamp — capture one with `date +%s` if you need it",
    "CI_PREV_PIPELINE_STATUS": "no previous-build context in GHA",
    "CI_PREV_COMMIT_SHA": "no previous-build context in GHA — use github.event.before on push events",
    "CI_MACHINE": "use ${{ runner.name }}",
}


def matches(key) -> bool:
    return False  # dispatched by the driver, not by a config key


def compat_env(ctx, report) -> dict:
    env: dict = {}
    for name in sorted(ctx.used_vars):
        if name in ctx.matrix_keys:  # a matrix axis, already defined from the matrix
            continue
        if name in COMPAT:
            env[name] = COMPAT[name]
            report.mapped(META.id, f"${name}", f"env.{name} = {COMPAT[name]}")
        elif name in NO_EQUIVALENT:
            report.manual(META.id, f"${name}", NO_EQUIVALENT[name])
        elif name.startswith("CI_PREV_"):
            report.manual(META.id, f"${name}", "no previous-build context in GHA")
        else:
            report.manual(META.id, f"${name}",
                          "not a Woodpecker built-in — if it is your own variable, define it "
                          "in env: or as a repository variable")
    return env
