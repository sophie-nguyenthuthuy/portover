# Migrate Azure Pipelines conditions to GitHub Actions if

**Directive:** `condition: and(succeeded(), eq(...))`

Part of the [azure-pipelines-to-gha](index.md) migration — `portover run azure-pipelines-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — azure-pipelines.yml (Azure Pipelines)

```yaml
condition: and(succeeded(), eq(variables['Build.SourceBranch'], 'refs/heads/main'))
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
if: success() && github.ref == 'refs/heads/main'
```

## What to watch for

Azure conditions are prefix functions, GHA expressions are infix, so portover parses the condition properly rather than pattern-matching it. Status checks translate directly: succeeded() -> success(), failed() -> failure(), always() -> always(), succeededOrFailed() -> always(). Watch the implicit default — an Azure job without a condition implicitly means succeeded(), while a GHA job with no `if:` also only runs when its needs succeeded, so the two agree. But adding ANY `if:` to a GHA job does NOT drop that implicit success check; `always()` is what overrides it, exactly as in Azure.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/condition.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
