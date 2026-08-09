"""publish / download — the artifact step shorthands."""

from portover.core import MappingMeta

SCOPE = "step"

META = MappingMeta(
    id="publish-download",
    directive="- publish: path / - download: current",
    title="Migrate Azure Pipelines publish and download shortcuts to GitHub Actions",
    before="""- publish: $(Build.ArtifactStagingDirectory)
  artifact: drop
- download: current
  artifact: drop""",
    after="""- uses: actions/upload-artifact@v4
  with:
    name: drop
    path: ${{ runner.temp }}
- uses: actions/download-artifact@v4
  with:
    name: drop""",
    notes=(
        "These are the short forms of PublishPipelineArtifact/"
        "DownloadPipelineArtifact and map to the same actions. Note "
        "`download: current` means artifacts from THIS run — the equivalent of "
        "download-artifact with no repository/run-id — while "
        "`download: <pipeline-resource>` pulls from another pipeline, which "
        "needs an explicit run-id or a cross-repo token and is flagged. "
        "$(Build.ArtifactStagingDirectory) has no exact GHA counterpart; "
        "${{ runner.temp }} is the closest scratch directory."
    ),
    priority=14,
)


def matches(name) -> bool:
    return name in ("publish", "download")


def apply(name, item, out, ctx, report) -> None:
    from portover.migrations.azure_pipelines_to_gha import rewrite_macros
    from portover.migrations.azure_pipelines_to_gha.expr import translate

    step: dict = {}
    if item.get("displayName"):
        step["name"] = str(item["displayName"])
    if item.get("condition") is not None:
        condition = translate(item["condition"], report, META.id)
        if condition:
            step["if"] = condition

    if name == "publish":
        path = rewrite_macros(str(item.get("publish", ".")), ctx, report)
        step["uses"] = "actions/upload-artifact@v4"
        step["with"] = {"name": str(item.get("artifact", "drop")), "path": path}
        report.mapped(META.id, f"publish: {item.get('publish')}", "actions/upload-artifact@v4")
    else:
        source = str(item.get("download", "current"))
        step["uses"] = "actions/download-artifact@v4"
        with_: dict = {}
        if item.get("artifact"):
            with_["name"] = str(item["artifact"])
        if item.get("path"):
            with_["path"] = rewrite_macros(str(item["path"]), ctx, report)
        if with_:
            step["with"] = with_
        if source != "current":
            report.manual(META.id, f"download: {source}",
                          "downloading from another pipeline — needs an explicit run-id "
                          "(and a token for another repo) on download-artifact")
        else:
            report.mapped(META.id, "download: current", "actions/download-artifact@v4")
    out.append(step)
