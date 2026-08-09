# Migrate Jenkins options to GitHub Actions

**Directive:** `options { timeout / disableConcurrentBuilds / buildDiscarder }`

Part of the [jenkins-to-gha](index.md) migration — `portover run jenkins-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — Jenkinsfile (declarative pipeline)

```groovy
options {
  timeout(time: 30, unit: 'MINUTES')
  disableConcurrentBuilds()
}
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: false
jobs:
  build:
    timeout-minutes: 30
```

## What to watch for

timeout -> per-job timeout-minutes. disableConcurrentBuilds -> a workflow concurrency group. buildDiscarder/logRotator has no YAML equivalent — retention lives in repo Settings > Actions. timestamps() is the GHA default and is dropped.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/options.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
