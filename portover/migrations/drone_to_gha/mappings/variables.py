"""$DRONE_* variables used in commands."""

from portover.core import MappingMeta

SCOPE = "transform"

META = MappingMeta(
    id="variables",
    directive="$DRONE_COMMIT_SHA, $DRONE_BRANCH, $DRONE_BUILD_NUMBER, ...",
    title="Migrate Drone environment variables to GitHub Actions",
    before="""commands:
  - docker build -t app:$DRONE_COMMIT_SHA .
  - echo "branch $DRONE_BRANCH build $DRONE_BUILD_NUMBER\"""",
    after="""env:   # added automatically, so the commands keep working unchanged
  DRONE_COMMIT_SHA: ${{ github.sha }}
  DRONE_BRANCH: ${{ github.ref_name }}
  DRONE_BUILD_NUMBER: ${{ github.run_number }}""",
    notes=(
        "Drone variables are plain shell variables, so portover defines the "
        "ones your commands actually reference as workflow-level `env:` from "
        "the github context and leaves the commands untouched. A few have no "
        "faithful equivalent and are flagged instead of invented: "
        "DRONE_COMMIT_SHA is a full SHA where some scripts want Drone's short "
        "form, DRONE_WORKSPACE points at /drone/src rather than the GHA "
        "workspace, and DRONE_BUILD_STATUS only exists inside Drone's own "
        "notification steps."
    ),
    priority=95,
)

COMPAT = {
    "CI": '"true"',
    "DRONE": '"true"',
    "DRONE_COMMIT": "${{ github.sha }}",
    "DRONE_COMMIT_SHA": "${{ github.sha }}",
    "DRONE_COMMIT_BRANCH": "${{ github.ref_name }}",
    "DRONE_COMMIT_MESSAGE": "${{ github.event.head_commit.message }}",
    "DRONE_COMMIT_AUTHOR": "${{ github.actor }}",
    "DRONE_COMMIT_REF": "${{ github.ref }}",
    "DRONE_BRANCH": "${{ github.ref_name }}",
    "DRONE_SOURCE_BRANCH": "${{ github.head_ref }}",
    "DRONE_TARGET_BRANCH": "${{ github.base_ref }}",
    "DRONE_TAG": "${{ github.ref_type == 'tag' && github.ref_name || '' }}",
    "DRONE_BUILD_NUMBER": "${{ github.run_number }}",
    "DRONE_BUILD_EVENT": "${{ github.event_name }}",
    "DRONE_BUILD_LINK": "${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}",
    "DRONE_REPO": "${{ github.repository }}",
    "DRONE_REPO_NAME": "${{ github.event.repository.name }}",
    "DRONE_REPO_OWNER": "${{ github.repository_owner }}",
    "DRONE_REPO_NAMESPACE": "${{ github.repository_owner }}",
    "DRONE_REPO_LINK": "${{ github.server_url }}/${{ github.repository }}",
    "DRONE_REPO_BRANCH": "${{ github.event.repository.default_branch }}",
    "DRONE_PULL_REQUEST": "${{ github.event.pull_request.number }}",
    "DRONE_STAGE_NAME": "${{ github.job }}",
    "DRONE_STEP_NAME": "${{ github.job }}",
    "DRONE_SYSTEM_HOST": "${{ github.server_url }}",
}

NO_EQUIVALENT = {
    "DRONE_COMMIT_SHA_SHORT": "GHA expressions cannot truncate — use `$(git rev-parse --short HEAD)`",
    "DRONE_WORKSPACE": "use ${{ github.workspace }} — there is no /drone/src on a GHA runner",
    "DRONE_BUILD_STATUS": "branch on ${{ job.status }}, or use if: success() / if: failure() steps",
    "DRONE_BUILD_STARTED": "no start timestamp — capture one with `date +%s` if you need it",
    "DRONE_BUILD_FINISHED": "no finish timestamp — capture one with `date +%s` if you need it",
    "DRONE_MACHINE": "use ${{ runner.name }}",
    "DRONE_RUNNER_HOST": "no runner host variable on hosted runners",
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
