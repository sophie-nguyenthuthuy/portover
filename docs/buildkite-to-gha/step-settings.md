# Migrate the remaining Buildkite step settings to GitHub Actions

**Directive:** `env / timeout_in_minutes / soft_fail / retry / concurrency / priority`

Part of the [buildkite-to-gha](index.md) migration — `portover run buildkite-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — Buildkite pipeline.yml

```yaml
env:
  DEPLOY_ENV: production
timeout_in_minutes: 30
soft_fail: true
concurrency: 1
concurrency_group: deploy
retry:
  automatic:
    limit: 2
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
env:
  DEPLOY_ENV: production
timeout-minutes: 30
continue-on-error: true       # soft_fail
concurrency:
  group: deploy
  cancel-in-progress: false
```

## What to watch for

Most are renames. Two are not: `soft_fail` with an `exit_status` list (tolerate only certain codes) has no equivalent — `continue-on-error` tolerates any failure — so handle specific codes in the command. And `retry.automatic` has no counterpart at job level; GHA offers re-running a failed job by hand, or wrapping the flaky command in a retry action, and neither can filter on Buildkite's exit-status conditions. `retry.manual` is simply the re-run button, which GHA has built in.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/step_settings.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
