# Migrate flake8 max-complexity to ruff

**Directive:** `max-complexity`

Part of the [flake8-to-ruff](index.md) migration — `portover run flake8-to-ruff` applies this mapping (and every other one on this page's index) automatically.

## Before — .flake8 / setup.cfg [flake8]

```ini
[flake8]
max-complexity = 10
```

## After — ruff.toml

```toml
[lint]
extend-select = ["C901"]

[lint.mccabe]
max-complexity = 10
```

## What to watch for

Setting the threshold is not enough in ruff — the C901 rule must also be selected, so portover adds it to extend-select.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/mccabe.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
