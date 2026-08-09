# Migrate Travis os and dist to GitHub Actions runs-on

**Directive:** `os / dist / arch`

Part of the [travis-to-gha](index.md) migration — `portover run travis-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .travis.yml (Travis CI)

```yaml
os:
  - linux
  - osx
dist: jammy
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
strategy:
  matrix:
    os: [ubuntu-22.04, macos-latest]
runs-on: ${{ matrix.os }}
```

## What to watch for

dist codenames pin the Ubuntu image (jammy -> ubuntu-22.04); EOL codenames fall back to ubuntu-latest with a flag. arm64/ppc64le/s390x arches need self-hosted or partner runners — flagged.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/os_dist.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
