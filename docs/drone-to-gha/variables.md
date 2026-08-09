# Migrate Drone environment variables to GitHub Actions

**Directive:** `$DRONE_COMMIT_SHA, $DRONE_BRANCH, $DRONE_BUILD_NUMBER, ...`

Part of the [drone-to-gha](index.md) migration — `portover run drone-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .drone.yml (Drone CI)

```yaml
commands:
  - docker build -t app:$DRONE_COMMIT_SHA .
  - echo "branch $DRONE_BRANCH build $DRONE_BUILD_NUMBER"
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
env:   # added automatically, so the commands keep working unchanged
  DRONE_COMMIT_SHA: ${{ github.sha }}
  DRONE_BRANCH: ${{ github.ref_name }}
  DRONE_BUILD_NUMBER: ${{ github.run_number }}
```

## What to watch for

Drone variables are plain shell variables, so portover defines the ones your commands actually reference as workflow-level `env:` from the github context and leaves the commands untouched. A few have no faithful equivalent and are flagged instead of invented: DRONE_COMMIT_SHA is a full SHA where some scripts want Drone's short form, DRONE_WORKSPACE points at /drone/src rather than the GHA workspace, and DRONE_BUILD_STATUS only exists inside Drone's own notification steps.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/variables.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
