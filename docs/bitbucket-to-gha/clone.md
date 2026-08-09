# Migrate Bitbucket Pipelines clone settings to GitHub Actions checkout

**Directive:** `clone: depth / lfs / enabled`

Part of the [bitbucket-to-gha](index.md) migration — `portover run bitbucket-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — bitbucket-pipelines.yml (Bitbucket Pipelines)

```yaml
clone:
  depth: full
  lfs: true
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
- uses: actions/checkout@v4
  with:
    fetch-depth: 0
    lfs: true
```

## What to watch for

The defaults differ and it matters: Bitbucket clones 50 commits, GHA clones 1. Anything reading history — `git describe`, changelog generation, a diff against the base branch — needs `fetch-depth: 0` even if the Bitbucket config never mentioned depth. `enabled: false` means the step gets no source at all, so portover emits no checkout.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/clone.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
