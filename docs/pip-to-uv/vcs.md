# Migrate pip git+https requirements to uv

**Directive:** `git+https://... (VCS requirement)`

Part of the [pip-to-uv](index.md) migration — `portover run pip-to-uv` applies this mapping (and every other one on this page's index) automatically.

## Before — requirements.txt (pip)

```text
git+https://github.com/psf/requests.git@v2.32.3#egg=requests
```

## After — pyproject.toml (uv)

```toml
dependencies = ["requests"]

[tool.uv.sources]
requests = { git = "https://github.com/psf/requests.git", rev = "v2.32.3" }
```

## What to watch for

The name moves to [project] dependencies, the URL to [tool.uv.sources]. @ref becomes rev; #subdirectory= becomes subdirectory. Only git sources are supported by uv — hg/svn/bzr are flagged for manual handling.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/vcs.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
