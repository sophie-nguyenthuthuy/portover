# Migrate pip -e (editable installs) to uv

**Directive:** `-e / --editable`

Part of the [pip-to-uv](index.md) migration — `portover run pip-to-uv` applies this mapping (and every other one on this page's index) automatically.

## Before — requirements.txt (pip)

```text
-e ./libs/mypkg
```

## After — pyproject.toml (uv)

```toml
dependencies = ["mypkg"]

[tool.uv.sources]
mypkg = { path = "libs/mypkg", editable = true }
```

## What to watch for

uv splits the dependency (name in [project]) from where it comes from ([tool.uv.sources]). `-e .` (the project itself) is simply not needed: uv always installs the current project editable inside its venv.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/editable.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
