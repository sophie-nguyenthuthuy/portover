# Migrate Buildkite pipeline-level settings to GitHub Actions

**Directive:** `env / agents / notify (pipeline level)`

Part of the [buildkite-to-gha](index.md) migration — `portover run buildkite-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — Buildkite pipeline.yml

```yaml
env:
  BUILD_MODE: release

agents:
  queue: builders

notify:
  - slack: "#builds"
  - github_commit_status:
      context: buildkite
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
env:
  BUILD_MODE: release        # workflow-level, visible to every job

# agents -> runs-on on each job
# notify -> a final job with if: always(), or GitHub's own
#           commit statuses (which Actions writes for free)
```

## What to watch for

Pipeline `env:` becomes workflow-level `env:`, the same scope. `agents:` is a default for every step and is copied onto each job's `runs-on`. `notify:` mostly disappears in a good way: `github_commit_status` and `github_check` exist because Buildkite is external to GitHub, whereas Actions writes commit statuses and checks natively — there is nothing to port. Slack, email and webhook notifications do need a step (with `if: failure()` for the common 'tell me when it breaks' case).

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/pipeline_settings.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
