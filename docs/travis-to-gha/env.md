# Migrate Travis env to GitHub Actions

**Directive:** `env / env.global / env.jobs (secure: ...)`

Part of the [travis-to-gha](index.md) migration — `portover run travis-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .travis.yml (Travis CI)

```yaml
env:
  global:
    - REGISTRY=ghcr.io/acme
    - secure: "encrypted..."
  jobs:
    - DB=postgres
    - DB=sqlite
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
env:
  REGISTRY: ghcr.io/acme
  API_KEY: ${{ secrets.API_KEY }}
strategy:
  matrix:
    env: ["DB=postgres", "DB=sqlite"]
steps:
  - run: tr " " "\n" <<< "${{ matrix.env }}" >> "$GITHUB_ENV"
```

## What to watch for

`secure:` values are Travis-encrypted and CANNOT be decrypted by anyone but Travis — re-create each one as a repository secret. A multi-row env list is a build matrix in Travis; portover reproduces it as a matrix dimension plus one step that loads the row into $GITHUB_ENV.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/env.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
