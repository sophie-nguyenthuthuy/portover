# Migrate Azure Pipelines jobs to GitHub Actions jobs

**Directive:** `jobs: [{job, dependsOn, condition, steps}] / steps:`

Part of the [azure-pipelines-to-gha](index.md) migration — `portover run azure-pipelines-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — azure-pipelines.yml (Azure Pipelines)

```yaml
jobs:
  - job: test
    displayName: Run tests
    dependsOn: build
    steps:
      - script: pytest -q
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
jobs:
  test:
    name: Run tests
    needs: build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pytest -q
```

## What to watch for

`dependsOn` becomes `needs` directly — unlike stages, Azure jobs run in PARALLEL by default, matching GHA, so only explicit dependencies carry over. `displayName` becomes `name`. A pipeline can also skip the jobs level entirely and write bare `steps:`, which becomes a single job called `build`. Deployment jobs (`- deployment:` with a `strategy: runOnce`) are converted as ordinary jobs pointing at a GHA Environment, since GHA has no separate deployment-job type.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/jobs.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
