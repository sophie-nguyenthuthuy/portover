# Migrate a CircleCI machine executor

**Directive:** `machine: {image: ...}`

Part of the [circleci-to-gha](index.md) migration — `portover run circleci-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .circleci/config.yml (CircleCI)

```yaml
machine:
  image: ubuntu-2204:current
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
runs-on: ubuntu-22.04
```

## What to watch for

CircleCI and GitHub runner images are not identical; validate installed tools after migration.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/machine.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
