# Migrate flake8 exclude to ruff

**Directive:** `exclude / extend-exclude`

Part of the [flake8-to-ruff](index.md) migration — `portover run flake8-to-ruff` applies this mapping (and every other one on this page's index) automatically.

## Before — .flake8 / setup.cfg [flake8]

```ini
[flake8]
exclude = .git,__pycache__,build,migrations
```

## After — ruff.toml

```toml
extend-exclude = ["build", "migrations"]
```

## What to watch for

ruff already excludes .git, __pycache__, virtualenvs and friends by default, so portover keeps only your non-default entries and uses extend-exclude to preserve the defaults.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/exclude.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
