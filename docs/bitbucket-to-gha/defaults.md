# Migrate Bitbucket Pipelines global settings to GitHub Actions

**Directive:** `image / clone / options (top level)`

Part of the [bitbucket-to-gha](index.md) migration — `portover run bitbucket-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — bitbucket-pipelines.yml (Bitbucket Pipelines)

```yaml
image: python:3.12

clone:
  depth: full
  lfs: true

options:
  max-time: 30
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
jobs:
  build:
    container: python:3.12          # copied into every job
    timeout-minutes: 30
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0           # depth: full
          lfs: true
```

## What to watch for

GHA has no pipeline-wide job defaults, so each of these is copied into every job, and a step that sets its own value wins — the same precedence Bitbucket uses. `clone.depth: full` is `fetch-depth: 0`, and a numeric depth maps straight across (Bitbucket defaults to 50, GHA to 1, so a script running `git log` or `git describe` may need this set explicitly). `clone.enabled: false` means no checkout at all.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/defaults.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
