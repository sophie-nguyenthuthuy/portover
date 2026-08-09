# Migrate Jenkins parameters to workflow_dispatch inputs

**Directive:** `parameters { string / booleanParam / choice }`

Part of the [jenkins-to-gha](index.md) migration — `portover run jenkins-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — Jenkinsfile (declarative pipeline)

```groovy
parameters {
  string(name: 'ENV', defaultValue: 'staging', description: 'target')
  booleanParam(name: 'DRY_RUN', defaultValue: true)
}
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
on:
  workflow_dispatch:
    inputs:
      ENV:
        type: string
        default: staging
        description: target
      DRY_RUN:
        type: boolean
        default: true
```

## What to watch for

Reference them as ${{ inputs.ENV }} instead of params.ENV. Unlike Jenkins, inputs only exist on manual runs — give push/schedule runs a fallback: ${{ inputs.ENV || 'staging' }}.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/parameters.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
