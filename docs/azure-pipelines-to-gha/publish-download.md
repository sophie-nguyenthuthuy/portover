# Migrate Azure Pipelines publish and download shortcuts to GitHub Actions

**Directive:** `- publish: path / - download: current`

Part of the [azure-pipelines-to-gha](index.md) migration — `portover run azure-pipelines-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — azure-pipelines.yml (Azure Pipelines)

```yaml
- publish: $(Build.ArtifactStagingDirectory)
  artifact: drop
- download: current
  artifact: drop
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
- uses: actions/upload-artifact@v4
  with:
    name: drop
    path: ${{ runner.temp }}
- uses: actions/download-artifact@v4
  with:
    name: drop
```

## What to watch for

These are the short forms of PublishPipelineArtifact/DownloadPipelineArtifact and map to the same actions. Note `download: current` means artifacts from THIS run — the equivalent of download-artifact with no repository/run-id — while `download: <pipeline-resource>` pulls from another pipeline, which needs an explicit run-id or a cross-repo token and is flagged. $(Build.ArtifactStagingDirectory) has no exact GHA counterpart; ${{ runner.temp }} is the closest scratch directory.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/publish_download.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
