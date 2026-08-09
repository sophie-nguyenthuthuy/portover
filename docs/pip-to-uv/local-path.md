# Migrate pip local path requirements to uv

**Directive:** `./local/pkg or wheel/sdist path`

Part of the [pip-to-uv](index.md) migration — `portover run pip-to-uv` applies this mapping (and every other one on this page's index) automatically.

## Before — requirements.txt (pip)

```text
./vendor/toolkit
dist/proto-1.2.0-py3-none-any.whl
```

## After — pyproject.toml (uv)

```toml
dependencies = ["toolkit", "proto"]

[tool.uv.sources]
toolkit = { path = "vendor/toolkit" }
proto = { path = "dist/proto-1.2.0-py3-none-any.whl" }
```

## What to watch for

Like every non-registry dep in uv: name in [project], location in [tool.uv.sources].

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/local_path.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
