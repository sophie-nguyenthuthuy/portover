# Migrate Travis language and version matrix to GitHub Actions

**Directive:** `language / python / node_js / go`

Part of the [travis-to-gha](index.md) migration — `portover run travis-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .travis.yml (Travis CI)

```yaml
language: python
python:
  - "3.11"
  - "3.12"
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
strategy:
  matrix:
    python: ["3.11", "3.12"]
steps:
  - uses: actions/setup-python@v5
    with:
      python-version: ${{ matrix.python }}
```

## What to watch for

One version -> plain setup step; several -> a matrix dimension named after the language. GHA runners preinstall many runtimes, but pinning via setup-* keeps the version explicit like Travis did.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/language.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
