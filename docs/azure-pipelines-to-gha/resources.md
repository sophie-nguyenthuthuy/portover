# Migrate Azure Pipelines resources, extends and name to GitHub Actions

**Directive:** `resources: repositories / containers / pipelines — plus extends and name`

Part of the [azure-pipelines-to-gha](index.md) migration — `portover run azure-pipelines-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — azure-pipelines.yml (Azure Pipelines)

```yaml
name: $(Date:yyyyMMdd)$(Rev:.r)

resources:
  repositories:
    - repository: templates
      type: git
      name: shared/ci-templates
  pipelines:
    - pipeline: upstream
      source: build-pipeline
      trigger: true

extends:
  template: templates/pipeline.yml@templates
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
run-name: build ${{ github.run_number }}

# repositories -> a second actions/checkout step with `repository:`
# pipelines (trigger) -> on: workflow_run
# extends -> a reusable workflow: uses: ./.github/workflows/pipeline.yml
```

## What to watch for

These are the keys that describe a pipeline's relationship to things outside the file, so none of them translate mechanically. `resources.repositories` becomes an extra actions/checkout step (with a token for private repos); `resources.pipelines` with `trigger: true` is `on: workflow_run`; `resources.containers` become job `container:`/`services:` entries. `extends:` means the real pipeline lives in another file — that is a reusable workflow in GHA, and portover cannot see the template's contents, so it is always flagged. `name:` is Azure's build-number format, whose closest counterpart is `run-name:` (though the $(Date)/$(Rev) tokens have no equivalent).

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/resources.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
