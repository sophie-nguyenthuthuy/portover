# Migrate flake8 select and ignore lists to ruff

**Directive:** `select / ignore / extend-select / extend-ignore`

Part of the [flake8-to-ruff](index.md) migration — `portover run flake8-to-ruff` applies this mapping (and every other one on this page's index) automatically.

## Before — .flake8 / setup.cfg [flake8]

```ini
[flake8]
extend-ignore = E203, W503
```

## After — ruff.toml

```toml
[lint]
extend-ignore = ["E203"]  # W503 does not exist in ruff
```

## What to watch for

pycodestyle/pyflakes codes (E/W/F) carry over 1:1. W503/W504 don't exist in ruff (its formatter settles the operator-break argument). Plugin codes move to ruff's re-implementations: B* needs flake8-bugbear -> select B, C4* -> C4, S* (bandit) -> S — enable those prefixes in [lint] select.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/select_ignore.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
