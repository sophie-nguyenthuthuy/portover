# Migrate CircleCI pipeline parameters to workflow_dispatch inputs

**Directive:** `parameters: (pipeline parameters)`

Part of the [circleci-to-gha](index.md) migration — `portover run circleci-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .circleci/config.yml (CircleCI)

```yaml
parameters:
  deploy_env:
    type: string
    default: staging
  run_slow_tests:
    type: boolean
    default: false
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
on:
  workflow_dispatch:
    inputs:
      deploy_env:
        type: string
        default: staging
      run_slow_tests:
        type: boolean
        default: false
```

## What to watch for

References change from `<< pipeline.parameters.deploy_env >>` to `${{ inputs.deploy_env }}` — portover rewrites those tokens inside run commands for you. Note the trigger difference: CircleCI parameters can be set by API-triggered pipelines, while workflow_dispatch inputs only exist on manual runs, so give push/schedule runs a fallback like `${{ inputs.deploy_env || 'staging' }}`.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/parameters.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
