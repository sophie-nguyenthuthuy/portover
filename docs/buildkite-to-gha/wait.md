# Migrate Buildkite wait steps to GitHub Actions needs

**Directive:** `- wait / - wait: {continue_on_failure: true}`

Part of the [buildkite-to-gha](index.md) migration — `portover run buildkite-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — Buildkite pipeline.yml

```yaml
steps:
  - label: Unit
    command: make unit
  - label: Lint
    command: make lint
  - wait
  - label: Deploy
    command: ./deploy.sh
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
jobs:
  unit:   { steps: [...] }     # no needs — parallel by default
  lint:   { steps: [...] }
  deploy:
    needs: [unit, lint]        # the wait barrier, expressed per job
    steps: [...]
```

## What to watch for

`wait` is the one construct with no GHA counterpart: GHA has no barrier, only per-job dependencies. portover therefore expands it — every step after the wait gains a `needs:` listing every step before it. That reproduces the ordering exactly, at the cost of a longer `needs:` list than a barrier would need. `continue_on_failure: true` (run the following steps even if earlier ones failed) becomes `if: always()` on those jobs, because a GHA job with `needs:` otherwise skips when a dependency fails.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/wait.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
