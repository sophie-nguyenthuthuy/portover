# Migrate plain requirements.txt lines to uv

**Directive:** `pkg==1.2, pkg[extra]>=2, pkg; python_version<"3.11"`

Part of the [pip-to-uv](index.md) migration — `portover run pip-to-uv` applies this mapping (and every other one on this page's index) automatically.

## Before — requirements.txt (pip)

```text
requests>=2.31
celery[redis]==5.4.0
tomli; python_version < "3.11"
```

## After — pyproject.toml (uv)

```toml
[project]
dependencies = [
    "requests>=2.31",
    "celery[redis]==5.4.0",
    'tomli; python_version < "3.11"',
]
```

## What to watch for

Specifiers, extras and environment markers are already PEP 508 — they move into [project] dependencies verbatim. Dev requirement files land in [dependency-groups] dev instead.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/requirement.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
