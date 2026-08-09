# Migrate Bitbucket Pipelines parallel steps to GitHub Actions

**Directive:** `- parallel: [steps] / - parallel: {fail-fast, steps}`

Part of the [bitbucket-to-gha](index.md) migration — `portover run bitbucket-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — bitbucket-pipelines.yml (Bitbucket Pipelines)

```yaml
- parallel:
    fail-fast: true
    steps:
      - step:
          name: Unit
          script: [make unit]
      - step:
          name: Lint
          script: [make lint]
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
jobs:
  unit:
    needs: build     # both siblings share the previous step's needs
    steps: [...]
  lint:
    needs: build
    steps: [...]
```

## What to watch for

The direction of the translation is inverted: Bitbucket runs steps sequentially and `parallel:` is how you opt into concurrency, while GHA runs jobs concurrently and `needs:` is how you opt into order. So a parallel block simply becomes sibling jobs that share the same `needs:`, and the step after the block needs all of them. `fail-fast` has no per-group equivalent — GHA's `strategy.fail-fast` only applies to a matrix — so with `fail-fast: false` the siblings keep running anyway (matching Bitbucket), and with `fail-fast: true` you would need to cancel the run yourself; portover flags that case.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/parallel.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
