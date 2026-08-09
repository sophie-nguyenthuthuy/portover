"""$(Build.*) and other predefined variables used in scripts."""

from portover.core import MappingMeta

SCOPE = "transform"  # a post-pass over the scripts, not a config key

META = MappingMeta(
    id="predefined-variables",
    directive="$(Build.SourceVersion), $(Build.SourceBranchName), $(Agent.OS), ...",
    title="Migrate Azure Pipelines predefined variables to GitHub Actions",
    before="""- script: |
    echo "building $(Build.SourceVersion) on $(Build.SourceBranchName)"
    docker build -t app:$(Build.BuildId) .
    echo "commit $(git rev-parse HEAD)\"""",
    after="""- run: |
    echo "building ${{ github.sha }} on ${{ github.ref_name }}"
    docker build -t app:${{ github.run_id }} .
    echo "commit $(git rev-parse HEAD)"   # left alone — shell substitution""",
    notes=(
        "Azure's `$(Name)` macro syntax collides with bash command "
        "substitution, and getting this wrong is silently destructive: leaving "
        "`$(Build.SourceVersion)` in a bash script makes the shell try to RUN a "
        "command called Build.SourceVersion. portover therefore rewrites a "
        "`$(...)` only when the name is dotted (a predefined variable) or "
        "declared in the pipeline's own `variables:` — so genuine command "
        "substitutions like `$(git rev-parse HEAD)` are left untouched. "
        "Variables with no faithful counterpart are flagged rather than "
        "invented: Build.ArtifactStagingDirectory and Build.BinariesDirectory "
        "(no such directories on a GHA runner — ${{ runner.temp }} is the "
        "closest) and Build.SourceVersionMessage."
    ),
    priority=95,
)

# Azure predefined variable (lowercased) -> GHA expression
COMPAT = {
    "build.sourceversion": "${{ github.sha }}",
    "build.sourcebranch": "${{ github.ref }}",
    "build.sourcebranchname": "${{ github.ref_name }}",
    "build.buildid": "${{ github.run_id }}",
    "build.buildnumber": "${{ github.run_number }}",
    "build.repository.name": "${{ github.repository }}",
    "build.repository.uri": "${{ github.server_url }}/${{ github.repository }}",
    "build.requestedfor": "${{ github.actor }}",
    "build.requestedforemail": "${{ github.actor }}",
    "build.definitionname": "${{ github.workflow }}",
    "build.reason": "${{ github.event_name }}",
    "build.sourcesdirectory": "${{ github.workspace }}",
    "system.defaultworkingdirectory": "${{ github.workspace }}",
    "system.pullrequest.pullrequestid": "${{ github.event.pull_request.number }}",
    "system.pullrequest.pullrequestnumber": "${{ github.event.pull_request.number }}",
    "system.pullrequest.sourcebranch": "${{ github.head_ref }}",
    "system.pullrequest.targetbranch": "${{ github.base_ref }}",
    "system.teamproject": "${{ github.repository_owner }}",
    "system.collectionuri": "${{ github.server_url }}",
    "agent.os": "${{ runner.os }}",
    "agent.osarchitecture": "${{ runner.arch }}",
    "agent.tempdirectory": "${{ runner.temp }}",
    "agent.toolsdirectory": "${{ runner.tool_cache }}",
    "agent.name": "${{ runner.name }}",
    "pipeline.workspace": "${{ github.workspace }}",
}

NO_EQUIVALENT = {
    "build.artifactstagingdirectory": "no staging directory on a GHA runner — use ${{ runner.temp }} or a path in the workspace",
    "build.binariesdirectory": "no binaries directory on a GHA runner — use a path in the workspace",
    "build.stagingdirectory": "no staging directory on a GHA runner — use ${{ runner.temp }}",
    "build.sourceversionmessage": "use ${{ github.event.head_commit.message }} (push events only)",
    "system.accesstoken": "use ${{ secrets.GITHUB_TOKEN }} — note it is scoped to this repository",
}


def matches(key) -> bool:
    return False  # dispatched by the driver, not by a config key


def reference(name: str) -> str:
    """The GHA text that replaces a `$(name)` macro."""
    key = name.lower()
    if key in COMPAT:
        return COMPAT[key]
    if key in NO_EQUIVALENT:
        return "${{ runner.temp }}" if "directory" in key else "${{ env.%s }}" % name.replace(".", "_")
    return "${{ env.%s }}" % name.replace(".", "_")


def compat_env(ctx, report) -> dict:
    """Report on every predefined macro the scripts referenced."""
    env: dict = {}
    for name in sorted(ctx.used_macros):
        key = name.lower()
        if key in COMPAT:
            report.mapped(META.id, f"$({name})", COMPAT[key])
        elif key in NO_EQUIVALENT:
            report.manual(META.id, f"$({name})", NO_EQUIVALENT[key])
        elif name in ctx.declared:
            report.mapped(META.id, f"$({name})", "${{ env.%s }} (pipeline variable)" % name)
        else:
            report.manual(META.id, f"$({name})", "unknown variable — define it in env: or drop the reference")
    return env
