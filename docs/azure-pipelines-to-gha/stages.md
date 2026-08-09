# Migrate Azure Pipelines stages to GitHub Actions

**Directive:** `stages: [{stage, dependsOn, condition, jobs}]`

Part of the [azure-pipelines-to-gha](index.md) migration — `portover run azure-pipelines-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — azure-pipelines.yml (Azure Pipelines)

```yaml
stages:
  - stage: Build
    jobs:
      - job: compile
        steps: [...]
  - stage: Deploy
    dependsOn: Build
    condition: succeeded()
    jobs:
      - job: ship
        steps: [...]
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
jobs:
  compile:
    steps: [...]
  ship:
    needs: compile        # inherited from the stage dependency
    if: success()
    steps: [...]
```

## What to watch for

GHA has no stage level, so stages are dissolved into their jobs. The ordering is preserved by giving each stage's entry jobs a `needs:` on every job of the stages it depends on — and remember Azure stages are sequential BY DEFAULT, so a stage with no `dependsOn` still waits for the previous one (`dependsOn: []` is how you opt out). A stage-level `condition:` is copied onto each job in that stage, and a stage-level `variables:` block becomes those jobs' env. Job ids only get a stage prefix when two stages reuse the same job name.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/stages.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
