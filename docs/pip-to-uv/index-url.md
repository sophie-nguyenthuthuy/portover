# Migrate pip --index-url and --extra-index-url to uv

**Directive:** `--index-url / --extra-index-url`

Part of the [pip-to-uv](index.md) migration — `portover run pip-to-uv` applies this mapping (and every other one on this page's index) automatically.

## Before — requirements.txt (pip)

```text
--index-url https://pypi.corp.example/simple
--extra-index-url https://pypi.org/simple
```

## After — pyproject.toml (uv)

```toml
[[tool.uv.index]]
name = "corp"
url = "https://pypi.corp.example/simple"
default = true

[[tool.uv.index]]
name = "pypi"
url = "https://pypi.org/simple"
```

## What to watch for

uv indexes are named and ordered; `default = true` replaces --index-url. Unlike pip, uv does not blend indexes per package by default (no dependency-confusion surprise) — pin a package to an index with [tool.uv.sources] pkg = { index = "corp" } if you need that.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/index_url.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
