# Migrate Azure Pipelines script steps to GitHub Actions

**Directive:** `- script / bash / pwsh / powershell / checkout`

Part of the [azure-pipelines-to-gha](index.md) migration — `portover run azure-pipelines-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — azure-pipelines.yml (Azure Pipelines)

```yaml
steps:
  - checkout: self
    fetchDepth: 0
  - script: pytest -q
    displayName: Run tests
    workingDirectory: backend
    env:
      TOKEN: $(SECRET_TOKEN)
  - bash: ./build.sh
    condition: succeeded()
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
steps:
  - uses: actions/checkout@v4
    with:
      fetch-depth: 0
  - name: Run tests
    run: pytest -q
    working-directory: backend
    env:
      TOKEN: ${{ env.SECRET_TOKEN }}
  - if: success()
    run: ./build.sh
```

## What to watch for

`script:` is cmd on Windows agents and bash elsewhere; `bash:`, `pwsh:` and `powershell:` pin the shell and map to GHA's `shell:` key. The default differs per platform in both systems, so a `script:` step that relied on cmd syntax on a Windows agent needs `shell: cmd` adding. `checkout: self` is the repo (actions/checkout), `checkout: none` skips it — and note GHA does NOT check out automatically, so a job with no checkout step still gets one from portover unless the pipeline said `none`.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/steps.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
