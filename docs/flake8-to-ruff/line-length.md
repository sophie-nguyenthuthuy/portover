# Migrate flake8 max-line-length to ruff

**Directive:** `max-line-length`

Part of the [flake8-to-ruff](index.md) migration — `portover run flake8-to-ruff` applies this mapping (and every other one on this page's index) automatically.

## Before — .flake8 / setup.cfg [flake8]

```ini
[flake8]
max-line-length = 100
```

## After — ruff.toml

```toml
line-length = 100
```

## What to watch for

Top-level key, shared by ruff's linter AND formatter. If you relied on flake8's B950-style 10% tolerance, that behaviour maps to E501 exactly, not loosely.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/line_length.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
