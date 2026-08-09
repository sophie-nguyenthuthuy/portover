# Migrate Azure Pipelines pipeline-level variables to GitHub Actions

**Directive:** `variables: (pipeline level)`

Part of the [azure-pipelines-to-gha](index.md) migration — `portover run azure-pipelines-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — azure-pipelines.yml (Azure Pipelines)

```yaml
variables:
  buildConfiguration: Release
  vmImageName: ubuntu-latest
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
env:
  buildConfiguration: Release
  vmImageName: ubuntu-latest
```

## What to watch for

Pipeline variables become workflow-level `env:`, visible to every job — the same scope Azure gives them. They are also what lets portover tell an Azure `$(macro)` apart from bash command substitution: a name declared here is rewritten in scripts, anything else is left alone. See the variables page for the group/template forms.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/pipeline_variables.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
