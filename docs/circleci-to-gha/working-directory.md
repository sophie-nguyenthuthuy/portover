# Migrate a CircleCI job working directory

**Directive:** `working_directory: path`

Part of the [circleci-to-gha](index.md) migration — `portover run circleci-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .circleci/config.yml (CircleCI)

```yaml
working_directory: ~/project/subdir
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
defaults:
  run:
    working-directory: subdir
```

## What to watch for

GHA paths are relative to the checked-out workspace; `~/project/` is removed.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/working_directory.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
