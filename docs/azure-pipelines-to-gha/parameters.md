# Migrate Azure Pipelines parameters to workflow_dispatch inputs

**Directive:** `parameters: [{name, type, default, values}]`

Part of the [azure-pipelines-to-gha](index.md) migration — `portover run azure-pipelines-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — azure-pipelines.yml (Azure Pipelines)

```yaml
parameters:
  - name: deployEnv
    type: string
    default: staging
    values: [staging, production]
  - name: runSlowTests
    type: boolean
    default: false
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
on:
  workflow_dispatch:
    inputs:
      deployEnv:
        type: choice
        default: staging
        options: [staging, production]
      runSlowTests:
        type: boolean
        default: false
```

## What to watch for

Both are run-time prompts, so this maps cleanly — a parameter with `values:` becomes a `choice` input with `options:`. The deeper difference is WHEN they are evaluated: Azure parameters are compile-time (`${{ parameters.x }}` can add or remove whole jobs before the run starts), while GHA inputs are run-time values only. A parameter used to conditionally include jobs therefore becomes an `if:` on those jobs, not a template expansion. Also note inputs exist only on manual runs — give push/schedule runs a fallback like `${{ inputs.deployEnv || 'staging' }}`.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/parameters.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
