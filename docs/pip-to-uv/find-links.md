# Migrate pip --find-links to uv

**Directive:** `--find-links / -f`

Part of the [pip-to-uv](index.md) migration — `portover run pip-to-uv` applies this mapping (and every other one on this page's index) automatically.

## Before — requirements.txt (pip)

```text
--find-links https://download.pytorch.org/whl/cpu
```

## After — pyproject.toml (uv)

```toml
[[tool.uv.index]]
name = "pytorch"
url = "https://download.pytorch.org/whl/cpu"
format = "flat"
```

## What to watch for

A flat (find-links style) listing becomes a uv index with format = "flat".

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/find_links.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
