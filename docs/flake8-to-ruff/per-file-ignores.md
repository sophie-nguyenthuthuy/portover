# Migrate flake8 per-file-ignores to ruff

**Directive:** `per-file-ignores`

Part of the [flake8-to-ruff](index.md) migration — `portover run flake8-to-ruff` applies this mapping (and every other one on this page's index) automatically.

## Before — .flake8 / setup.cfg [flake8]

```ini
[flake8]
per-file-ignores =
    tests/*: S101,D103
    __init__.py: F401
```

## After — ruff.toml

```toml
[lint.per-file-ignores]
"tests/*" = ["S101", "D103"]
"__init__.py" = ["F401"]
```

## What to watch for

Same pattern:codes idea, TOML table instead of ini lines. Patterns are quoted TOML keys.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/per_file_ignores.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
