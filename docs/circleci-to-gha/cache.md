# Migrate CircleCI caches

**Directive:** `- restore_cache / save_cache`

Part of the [circleci-to-gha](index.md) migration — `portover run circleci-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .circleci/config.yml (CircleCI)

```yaml
- restore_cache:
    keys: [v1-deps-{{ checksum "requirements.txt" }}, v1-deps-]
- save_cache:
    key: v1-deps-{{ checksum "requirements.txt" }}
    paths: [.venv]
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
- uses: actions/cache@v4
  with:
    path: .venv
    key: v1-deps-${{ hashFiles('requirements.txt') }}
    restore-keys: v1-deps-
```

## What to watch for

GHA combines restore and save in one action. A restore-only step has no path in CircleCI, so portover flags it for completion.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/cache.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
