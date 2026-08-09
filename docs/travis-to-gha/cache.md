# Migrate Travis cache to GitHub Actions

**Directive:** `cache: pip / npm / directories`

Part of the [travis-to-gha](index.md) migration — `portover run travis-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .travis.yml (Travis CI)

```yaml
cache: pip
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
- uses: actions/setup-python@v5
  with:
    python-version: "3.12"
    cache: pip
```

## What to watch for

Package-manager caches are built into the setup-* actions (one line). cache: directories becomes actions/cache — pick a real key: portover uses a lockfile hash placeholder you must point at your actual dependency file.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/cache.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
