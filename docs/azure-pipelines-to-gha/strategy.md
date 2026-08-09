# Migrate Azure Pipelines strategy matrix to GitHub Actions

**Directive:** `strategy: matrix / parallel / maxParallel`

Part of the [azure-pipelines-to-gha](index.md) migration — `portover run azure-pipelines-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — azure-pipelines.yml (Azure Pipelines)

```yaml
strategy:
  matrix:
    Python311:
      python.version: "3.11"
    Python312:
      python.version: "3.12"
  maxParallel: 2
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
strategy:
  max-parallel: 2
  matrix:
    include:
      - python_version: "3.11"
      - python_version: "3.12"
```

## What to watch for

The shapes differ: Azure names each combination explicitly (a mapping of legName -> variables) while GHA takes axes and multiplies them. Named legs are therefore emitted as matrix `include:` rows, which reproduces exactly the combinations listed rather than a cartesian product. Dots in Azure variable names (`python.version`) are not valid in GHA matrix keys, so they become underscores — update the references in your scripts to match. `maxParallel` is `max-parallel`; a plain `parallel: N` (slicing one job across agents) has no equivalent and is flagged.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/strategy.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
