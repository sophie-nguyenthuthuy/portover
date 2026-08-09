# Migrate pip --hash pinned requirements to uv

**Directive:** `pkg==1.2 --hash=sha256:...`

Part of the [pip-to-uv](index.md) migration — `portover run pip-to-uv` applies this mapping (and every other one on this page's index) automatically.

## Before — requirements.txt (pip)

```text
requests==2.32.3 --hash=sha256:5559... --hash=sha256:9a38...
```

## After — pyproject.toml (uv)

```toml
dependencies = ["requests==2.32.3"]
# hashes live in uv.lock — generated, verified on install, never hand-edited
```

## What to watch for

Hash-pinned files are usually pip-compile output. Point portover at the *source* requirements.in if you have one; either way uv.lock takes over hash pinning the moment you run `uv lock`.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/hashes.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
