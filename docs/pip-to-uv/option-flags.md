# Migrate pip --pre, --no-binary and --only-binary to uv

**Directive:** `--pre / --no-binary / --only-binary`

Part of the [pip-to-uv](index.md) migration — `portover run pip-to-uv` applies this mapping (and every other one on this page's index) automatically.

## Before — requirements.txt (pip)

```text
--pre
--no-binary grpcio
--only-binary numpy
```

## After — pyproject.toml (uv)

```toml
[tool.uv]
prerelease = "allow"
no-binary-package = ["grpcio"]
no-build-package = ["numpy"]
```

## What to watch for

`--no-binary :all:` becomes `no-binary = true`; `--only-binary :all:` becomes `no-build = true`. Per-package lists map to the *-package keys.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/option_flags.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
