# Migrate pip -r includes and -c constraints to uv

**Directive:** `-r file / -c file`

Part of the [pip-to-uv](index.md) migration — `portover run pip-to-uv` applies this mapping (and every other one on this page's index) automatically.

## Before — requirements.txt (pip)

```text
-r base.txt
-c constraints.txt
```

## After — pyproject.toml (uv)

```toml
# includes disappear: uv reads everything from pyproject.toml
[tool.uv]
constraint-dependencies = ["grpcio<1.60"]  # contents of constraints.txt
```

## What to watch for

uv has no include chain — run portover in each directory or merge the included files first. `-c` maps to `[tool.uv] constraint-dependencies`, which takes the *contents* of the constraints file, not its path.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/include.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
