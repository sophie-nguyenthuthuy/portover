# Migrate Drone trigger to GitHub Actions

**Directive:** `trigger: branch / event / ref / cron`

Part of the [drone-to-gha](index.md) migration — `portover run drone-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .drone.yml (Drone CI)

```yaml
trigger:
  branch:
    - main
  event:
    - push
    - tag
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
on:
  push:
    branches: [main]
    tags: ["*"]

jobs:
  default:
    if: github.ref_name == 'main'   # kept per job, see below
```

## What to watch for

A Drone trigger is per PIPELINE, while GHA triggers are per WORKFLOW file — and one .drone.yml can hold several pipelines with different triggers. portover therefore does both: it widens the workflow's `on:` to cover every pipeline's events, and keeps each pipeline's own conditions as an `if:` on its job. That combination fires the same runs Drone would. `event: tag` adds `on: push: tags:` — without a tag trigger the job's `if:` could never fire. `cron:` names a Drone-side schedule that is not in this file, so it is flagged.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/trigger.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
