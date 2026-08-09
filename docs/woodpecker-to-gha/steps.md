# Migrate Woodpecker steps to GitHub Actions

**Directive:** `steps: (list or map) — also the older `pipeline:` key`

Part of the [woodpecker-to-gha](index.md) migration — `portover run woodpecker-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .woodpecker.yml (Woodpecker CI)

```yaml
steps:                        # list form
  - name: build
    image: golang:1.22
    commands: [go build]

steps:                        # map form — equally valid
  build:
    image: golang:1.22
    commands: [go build]
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
jobs:
  woodpecker:
    container: golang:1.22
    steps:
      - uses: actions/checkout@v4
      - name: build
        run: go build
```

## What to watch for

Woodpecker accepts both spellings — a list where each entry carries `name:`, and a map keyed by step name — so portover normalises them before converting. Older configs use `pipeline:` instead of `steps:`, which is handled identically. Steps share the workspace volume, which is GHA step behaviour, so they become steps of one job rather than separate jobs. Per-step images are the mismatch: GHA containers are per job, so a shared image becomes `container:` while differing images run through `docker run` with the workspace bind-mounted.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/steps.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
