# Migrate Azure Pipelines templates to GitHub Actions

**Directive:** `- template: steps/build.yml@repo`

Part of the [azure-pipelines-to-gha](index.md) migration — `portover run azure-pipelines-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — azure-pipelines.yml (Azure Pipelines)

```yaml
steps:
  - template: templates/build-steps.yml
    parameters:
      buildConfig: Release
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
steps:
  # a step template is closest to a composite action:
  - uses: ./.github/actions/build-steps
    with:
      buildConfig: Release
```

## What to watch for

portover only reads the file you point it at, so a template's contents are NOT in the output — this is always a manual step. The mapping depends on what the template holds: STEP templates become composite actions (.github/actions/<name>/action.yml, called with `uses: ./...`), while JOB and STAGE templates become reusable workflows (`on: workflow_call`, called with `uses: ./.github/workflows/x.yml`). Template `parameters:` become the action's `inputs:` in both cases. An `extends:` template at the top of a pipeline is the whole pipeline's shape and usually needs rethinking rather than translating.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/template.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
