# Migrate Woodpecker CI_ variables to GitHub Actions

**Directive:** `$CI_COMMIT_SHA, $CI_COMMIT_BRANCH, $CI_PIPELINE_NUMBER, ...`

Part of the [woodpecker-to-gha](index.md) migration — `portover run woodpecker-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .woodpecker.yml (Woodpecker CI)

```yaml
commands:
  - docker build -t app:$CI_COMMIT_SHA .
  - echo "branch $CI_COMMIT_BRANCH pipeline $CI_PIPELINE_NUMBER"
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
env:   # added automatically, so the commands keep working unchanged
  CI_COMMIT_SHA: ${{ github.sha }}
  CI_COMMIT_BRANCH: ${{ github.ref_name }}
  CI_PIPELINE_NUMBER: ${{ github.run_number }}
```

## What to watch for

Woodpecker uses the CI_ prefix where Drone used DRONE_ (2.0 dropped the DRONE_ aliases entirely), and they are plain shell variables — so portover defines the ones your commands reference as workflow-level `env:` from the github context and leaves the commands untouched. Note CI_ is a broad prefix: a variable that is not a Woodpecker built-in is reported rather than invented, since it is probably one of your own and needs defining. CI_WORKSPACE points at /woodpecker/src rather than the GHA workspace, and CI_PREV_* (previous build) has no counterpart at all.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/ci_variables.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
