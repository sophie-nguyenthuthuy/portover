# Migrate Azure Pipelines pr triggers to GitHub Actions

**Directive:** `pr: branches / paths / drafts / none`

Part of the [azure-pipelines-to-gha](index.md) migration — `portover run azure-pipelines-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — azure-pipelines.yml (Azure Pipelines)

```yaml
pr:
  branches:
    include: [main]
  drafts: false
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
on:
  pull_request:
    branches: [main]
    # drafts: filter with
    # if: github.event.pull_request.draft == false
```

## What to watch for

`pr.branches` filters the TARGET branch, same as GHA's `pull_request.branches` — a common misreading is to think it filters the source branch. `drafts: false` has no trigger-level equivalent: GHA runs on draft PRs, so add `if: github.event.pull_request.draft == false` to the jobs. `pr: none` disables PR validation entirely.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/pr.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
