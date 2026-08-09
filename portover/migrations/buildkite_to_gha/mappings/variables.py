"""$BUILDKITE_* variables and the buildkite-agent CLI."""

from portover.core import MappingMeta

SCOPE = "transform"

META = MappingMeta(
    id="variables",
    directive="$BUILDKITE_COMMIT, $BUILDKITE_BRANCH, buildkite-agent ...",
    title="Migrate Buildkite variables and the buildkite-agent CLI to GitHub Actions",
    before="""commands:
  - docker build -t app:$BUILDKITE_COMMIT .
  - buildkite-agent artifact upload "dist/**"
  - buildkite-agent annotate "deployed" --style success""",
    after="""env:   # added automatically, so the scripts keep working
  BUILDKITE_COMMIT: ${{ github.sha }}

# buildkite-agent has no counterpart binary:
- uses: actions/upload-artifact@v4      # artifact upload
  with: {name: build, path: dist/**}
- run: echo "deployed" >> "$GITHUB_STEP_SUMMARY"   # annotate""",
    notes=(
        "Variables are plain shell variables, so portover defines the ones "
        "your commands actually use as workflow-level `env:` from the github "
        "context and leaves the commands untouched. The `buildkite-agent` CLI "
        "is the sharper edge: it is installed on every Buildkite agent and "
        "does not exist on a GHA runner, so any command using it fails at "
        "runtime rather than at conversion. The mappings are "
        "`artifact upload` -> actions/upload-artifact, `artifact download` -> "
        "actions/download-artifact, `annotate` -> writing to "
        "$GITHUB_STEP_SUMMARY, `meta-data set/get` -> job outputs "
        "(`>> \"$GITHUB_OUTPUT\"` and `needs.<job>.outputs.<name>`), and "
        "`pipeline upload` (dynamic pipelines) -> a matrix built with "
        "fromJSON, since GHA cannot add jobs mid-run."
    ),
    priority=95,
)

COMPAT = {
    "CI": '"true"',
    "BUILDKITE_COMMIT": "${{ github.sha }}",
    "BUILDKITE_BRANCH": "${{ github.ref_name }}",
    "BUILDKITE_TAG": "${{ github.ref_type == 'tag' && github.ref_name || '' }}",
    "BUILDKITE_MESSAGE": "${{ github.event.head_commit.message }}",
    "BUILDKITE_BUILD_NUMBER": "${{ github.run_number }}",
    "BUILDKITE_BUILD_ID": "${{ github.run_id }}",
    "BUILDKITE_BUILD_URL": "${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}",
    "BUILDKITE_JOB_ID": "${{ github.job }}",
    "BUILDKITE_LABEL": "${{ github.job }}",
    "BUILDKITE_PIPELINE_SLUG": "${{ github.workflow }}",
    "BUILDKITE_PIPELINE_NAME": "${{ github.workflow }}",
    "BUILDKITE_PIPELINE_DEFAULT_BRANCH": "${{ github.event.repository.default_branch }}",
    "BUILDKITE_ORGANIZATION_SLUG": "${{ github.repository_owner }}",
    "BUILDKITE_REPO": "${{ github.server_url }}/${{ github.repository }}",
    "BUILDKITE_BUILD_CHECKOUT_PATH": "${{ github.workspace }}",
    "BUILDKITE_PULL_REQUEST": "${{ github.event.pull_request.number }}",
    "BUILDKITE_PULL_REQUEST_BASE_BRANCH": "${{ github.base_ref }}",
    "BUILDKITE_BUILD_CREATOR": "${{ github.actor }}",
    "BUILDKITE_BUILD_CREATOR_EMAIL": "${{ github.actor }}",
    "BUILDKITE_SOURCE": "${{ github.event_name }}",
    "BUILDKITE_RETRY_COUNT": "${{ github.run_attempt }}",
}

NO_EQUIVALENT = {
    "BUILDKITE_AGENT_NAME": "use ${{ runner.name }}",
    "BUILDKITE_AGENT_ID": "no agent identity on hosted runners",
    "BUILDKITE_COMMAND_EXIT_STATUS": "branch on ${{ job.status }}, or split into if: success() / if: failure() steps",
    "BUILDKITE_ARTIFACT_PATHS": "artifact paths are given per upload-artifact step",
    "BUILDKITE_PARALLEL_JOB": "set by the matrix mapping when a step uses parallelism:",
    "BUILDKITE_PARALLEL_JOB_COUNT": "set by the matrix mapping when a step uses parallelism:",
    "BUILDKITE_PLUGIN_CONFIGURATION": "plugin config has no runtime equivalent",
}


def matches(key) -> bool:
    return False  # dispatched by the driver, not by a config key


def compat_env(ctx, report) -> dict:
    env: dict = {}
    for name in sorted(ctx.used_vars):
        if name in ctx.provided_vars:  # already defined by the step that needs it
            report.mapped(META.id, f"${name}", "defined from the job matrix")
            continue
        if name in COMPAT:
            env[name] = COMPAT[name]
            report.mapped(META.id, f"${name}", f"env.{name} = {COMPAT[name]}")
        elif name in NO_EQUIVALENT:
            report.manual(META.id, f"${name}", NO_EQUIVALENT[name])
        else:
            report.manual(META.id, f"${name}", "no GHA equivalent — define it in env: or drop the reference")
    if ctx.uses_agent_cli:
        report.manual(META.id, "buildkite-agent (CLI)",
                      "the buildkite-agent binary does not exist on a GHA runner — replace "
                      "`artifact upload/download` with actions/upload-artifact and "
                      "actions/download-artifact, `annotate` with a write to "
                      '"$GITHUB_STEP_SUMMARY", and `meta-data` with job outputs')
    return env
