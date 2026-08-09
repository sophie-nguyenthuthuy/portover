# Migrate GitLab CI parallel to GitHub Actions matrix

**Directive:** `parallel: N / parallel: matrix:`

Part of the [gitlab-ci-to-gha](index.md) migration — `portover run gitlab-ci-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .gitlab-ci.yml (GitLab CI)

```yaml
parallel:
  matrix:
    - PYTHON: ["3.11", "3.12"]
      OS: [linux]

# or a plain count:
parallel: 4
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
strategy:
  matrix:
    PYTHON: ["3.11", "3.12"]
    OS: [linux]

# a plain count becomes an index matrix:
strategy:
  matrix:
    CI_NODE_INDEX: [1, 2, 3, 4]
env:
  CI_NODE_TOTAL: 4
```

## What to watch for

`parallel: matrix:` maps onto `strategy.matrix` almost exactly — the difference is that GitLab takes a LIST of variable sets (each entry is its own product) while GHA takes one mapping plus `include:`, so portover puts the first entry in the matrix and the rest under `include:`. A plain `parallel: N` splits one job across N runners, and the split only works because GitLab sets CI_NODE_INDEX/CI_NODE_TOTAL for your test runner to shard on — portover recreates both from the matrix so the existing command keeps working.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/parallel.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
