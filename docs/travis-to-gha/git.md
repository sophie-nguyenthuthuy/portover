# Migrate Travis git options to GitHub Actions checkout

**Directive:** `git: depth / submodules / lfs_skip_smudge`

Part of the [travis-to-gha](index.md) migration — `portover run travis-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .travis.yml (Travis CI)

```yaml
git:
  depth: false
  submodules: true
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
- uses: actions/checkout@v4
  with:
    fetch-depth: 0
    submodules: true
```

## What to watch for

depth: false means full history -> fetch-depth: 0 (checkout's default is a shallow depth 1, same spirit as Travis' default 50). lfs_skip_smudge inverts into `lfs: true` on checkout when you DO want LFS files.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/git.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
