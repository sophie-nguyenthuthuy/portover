# Migrate Travis branches to GitHub Actions on.push.branches

**Directive:** `branches: only / except`

Part of the [travis-to-gha](index.md) migration — `portover run travis-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .travis.yml (Travis CI)

```yaml
branches:
  only:
    - main
    - /^release-.*$/
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
on:
  push:
    branches: [main, "release-*"]
  pull_request:
```

## What to watch for

Travis regexes (/.../) become glob patterns — portover converts the common ^prefix-.*$ shape and flags anything fancier. `except` maps to branches-ignore. PRs: Travis built PRs regardless of this setting, so `pull_request:` is kept unfiltered.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/branches.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
