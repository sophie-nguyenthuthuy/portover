"""$BITBUCKET_* predefined variables used in scripts."""

from portover.core import MappingMeta

SCOPE = "transform"  # a post-pass over the scripts, not a config key

META = MappingMeta(
    id="variables",
    directive="$BITBUCKET_COMMIT, $BITBUCKET_BRANCH, $BITBUCKET_BUILD_NUMBER, ...",
    title="Migrate Bitbucket Pipelines variables to GitHub Actions",
    before="""script:
  - docker build -t app:$BITBUCKET_COMMIT .
  - echo "on branch $BITBUCKET_BRANCH build $BITBUCKET_BUILD_NUMBER\"""",
    after="""env:   # added automatically, so the scripts keep working unchanged
  BITBUCKET_COMMIT: ${{ github.sha }}
  BITBUCKET_BRANCH: ${{ github.ref_name }}
  BITBUCKET_BUILD_NUMBER: ${{ github.run_number }}""",
    notes=(
        "Bitbucket variables are plain shell variables, so rather than editing "
        "every command (and risking a bad edit inside a quoted string), "
        "portover defines the ones your scripts actually use as workflow-level "
        "`env:` sourced from the github context. The scripts migrate "
        "byte-for-byte. Only referenced variables are defined. Two have no "
        "faithful equivalent and are flagged: $BITBUCKET_COMMIT is a full SHA "
        "while some scripts expect Bitbucket's shortened form, and "
        "$BITBUCKET_REPO_OWNER-style identity variables differ. Repository "
        "variables you set in Bitbucket's UI are not in this file at all — "
        "recreate them as GitHub secrets."
    ),
    priority=95,
)

COMPAT = {
    "CI": '"true"',
    "BITBUCKET_COMMIT": "${{ github.sha }}",
    "BITBUCKET_BRANCH": "${{ github.ref_name }}",
    "BITBUCKET_TAG": "${{ github.ref_type == 'tag' && github.ref_name || '' }}",
    "BITBUCKET_BUILD_NUMBER": "${{ github.run_number }}",
    "BITBUCKET_REPO_SLUG": "${{ github.event.repository.name }}",
    "BITBUCKET_REPO_FULL_NAME": "${{ github.repository }}",
    "BITBUCKET_REPO_OWNER": "${{ github.repository_owner }}",
    "BITBUCKET_WORKSPACE": "${{ github.repository_owner }}",
    "BITBUCKET_CLONE_DIR": "${{ github.workspace }}",
    "BITBUCKET_GIT_HTTP_ORIGIN": "${{ github.server_url }}/${{ github.repository }}",
    "BITBUCKET_PR_ID": "${{ github.event.pull_request.number }}",
    "BITBUCKET_PR_DESTINATION_BRANCH": "${{ github.base_ref }}",
    "BITBUCKET_DEPLOYMENT_ENVIRONMENT": "${{ github.event.deployment.environment }}",
    "BITBUCKET_STEP_TRIGGERER_UUID": "${{ github.actor }}",
    "BITBUCKET_PROJECT_KEY": "${{ github.repository_owner }}",
}

NO_EQUIVALENT = {
    "BITBUCKET_EXIT_CODE": "in an after-script, branch on ${{ job.status }} or split into if: success() / if: failure() steps",
    "BITBUCKET_STEP_UUID": "no per-step identifier — use ${{ github.job }}",
    "BITBUCKET_PIPELINE_UUID": "use ${{ github.run_id }}",
    "BITBUCKET_SSH_KEY_FILE": "no managed SSH key — add the key as a secret and load it with webfactory/ssh-agent",
    "BITBUCKET_STEP_OIDC_TOKEN": "request the OIDC token via the actions toolkit, or use a cloud login action",
}


def matches(key) -> bool:
    return False  # dispatched by the driver, not by a config key


def compat_env(ctx, report) -> dict:
    env: dict = {}
    for name in sorted(ctx.used_vars):
        if name in COMPAT:
            env[name] = COMPAT[name]
            report.mapped(META.id, f"${name}", f"env.{name} = {COMPAT[name]}")
        elif name in NO_EQUIVALENT:
            report.manual(META.id, f"${name}", NO_EQUIVALENT[name])
        else:
            report.manual(META.id, f"${name}",
                          "no GHA equivalent — define it in env: or drop the reference")
    return env
