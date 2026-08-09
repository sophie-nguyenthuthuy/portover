# Migrate CircleCI reusable executors to GitHub Actions

**Directive:** `executors: (reusable executors)`

Part of the [circleci-to-gha](index.md) migration — `portover run circleci-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .circleci/config.yml (CircleCI)

```yaml
executors:
  py:
    docker:
      - image: cimg/python:3.12

jobs:
  test:
    executor: py
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    container: cimg/python:3.12
```

## What to watch for

GHA has no named-executor concept, so portover resolves the reference and writes the runner/container inline in every job that used it. If several jobs share one executor and you want to keep that DRY, a reusable workflow (workflow_call) is the closest equivalent.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/executors.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
