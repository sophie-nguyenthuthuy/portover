# Migrate a CircleCI reusable executor reference

**Directive:** `executor: <name>`

Part of the [circleci-to-gha](index.md) migration — `portover run circleci-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .circleci/config.yml (CircleCI)

```yaml
executor: python-executor
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
runs-on: ubuntu-latest
container: cimg/python:3.12
```

## What to watch for

The named executor is expanded inline because GHA jobs cannot refer to a shared executor block.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/executor.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
