# Migrate Azure Pipelines predefined variables to GitHub Actions

**Directive:** `$(Build.SourceVersion), $(Build.SourceBranchName), $(Agent.OS), ...`

Part of the [azure-pipelines-to-gha](index.md) migration — `portover run azure-pipelines-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — azure-pipelines.yml (Azure Pipelines)

```yaml
- script: |
    echo "building $(Build.SourceVersion) on $(Build.SourceBranchName)"
    docker build -t app:$(Build.BuildId) .
    echo "commit $(git rev-parse HEAD)"
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
- run: |
    echo "building ${{ github.sha }} on ${{ github.ref_name }}"
    docker build -t app:${{ github.run_id }} .
    echo "commit $(git rev-parse HEAD)"   # left alone — shell substitution
```

## What to watch for

Azure's `$(Name)` macro syntax collides with bash command substitution, and getting this wrong is silently destructive: leaving `$(Build.SourceVersion)` in a bash script makes the shell try to RUN a command called Build.SourceVersion. portover therefore rewrites a `$(...)` only when the name is dotted (a predefined variable) or declared in the pipeline's own `variables:` — so genuine command substitutions like `$(git rev-parse HEAD)` are left untouched. Variables with no faithful counterpart are flagged rather than invented: Build.ArtifactStagingDirectory and Build.BinariesDirectory (no such directories on a GHA runner — ${{ runner.temp }} is the closest) and Build.SourceVersionMessage.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/predefined_variables.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
