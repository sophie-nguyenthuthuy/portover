# Migrate Azure Pipelines job settings to GitHub Actions

**Directive:** `container / services / timeoutInMinutes / continueOnError / workspace`

Part of the [azure-pipelines-to-gha](index.md) migration — `portover run azure-pipelines-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — azure-pipelines.yml (Azure Pipelines)

```yaml
container: python:3.12
services:
  db: postgres
timeoutInMinutes: 30
continueOnError: true
workspace:
  clean: all
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
container: python:3.12
services:
  db:
    image: postgres
timeout-minutes: 30
continue-on-error: true
# workspace.clean: dropped — GHA jobs always start clean
```

## What to watch for

Mostly direct renames. Two notes: the default timeout differs sharply (Azure gives Microsoft-hosted jobs 60 minutes, GHA gives 360), so a job that relied on Azure's default to kill a hang now runs six times longer — set it explicitly if it mattered. And `workspace: clean:` is unnecessary: every GHA job starts on a fresh runner, which is why `clean: all` has nothing to do.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/job_settings.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
