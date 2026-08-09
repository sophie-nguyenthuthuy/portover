# Migrate Azure Pipelines schedules to GitHub Actions

**Directive:** `schedules: [{cron, branches, always}]`

Part of the [azure-pipelines-to-gha](index.md) migration — `portover run azure-pipelines-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — azure-pipelines.yml (Azure Pipelines)

```yaml
schedules:
  - cron: "0 3 * * *"
    displayName: Nightly
    branches:
      include: [main]
    always: true
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
on:
  schedule:
    - cron: "0 3 * * *"
```

## What to watch for

The cron syntax is identical (both UTC, both 5-field). What does not carry over is the branch filter: an Azure schedule names the branches to build, while a GHA scheduled run ALWAYS uses the default branch — there is no way to schedule a different branch, so a schedule for a non-default branch needs rethinking. `always: false` (skip when there are no new commits) also has no equivalent; GHA runs the schedule regardless.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/schedules.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
