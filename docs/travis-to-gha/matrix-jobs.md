# Migrate Travis jobs and matrix customization to GitHub Actions

**Directive:** `jobs/matrix: include / exclude / allow_failures / fast_finish`

Part of the [travis-to-gha](index.md) migration — `portover run travis-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .travis.yml (Travis CI)

```yaml
jobs:
  include:
    - python: "3.13"
      env: EXPERIMENTAL=1
  allow_failures:
    - python: "3.13"
  fast_finish: true
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
strategy:
  fail-fast: true
  matrix:
    include:
      - python: "3.13"
        env: EXPERIMENTAL=1
# allow_failures: add to the job
#   continue-on-error: ${{ matrix.python == '3.13' }}
```

## What to watch for

include/exclude rows carry over almost 1:1 (env strings stay strings; load them like the env matrix rows). allow_failures has no direct key — it becomes a continue-on-error expression on the job, which portover writes for single-key rows and flags otherwise. fast_finish is fail-fast (GHA's default is already true). `stage:` grouping needs separate jobs with needs: — flagged.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/matrix_jobs.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
