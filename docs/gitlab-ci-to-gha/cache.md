# Migrate GitLab CI cache to GitHub Actions

**Directive:** `cache: key / paths / policy`

Part of the [gitlab-ci-to-gha](index.md) migration — `portover run gitlab-ci-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .gitlab-ci.yml (GitLab CI)

```yaml
cache:
  key:
    files:
      - requirements.txt
  paths:
    - .cache/pip
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
- uses: actions/cache@v4
  with:
    path: .cache/pip
    key: ${{ runner.os }}-${{ hashFiles('requirements.txt') }}
```

## What to watch for

`key: files:` is the same idea as `hashFiles()` and translates directly. A plain string key translates too, but watch out: GitLab *overwrites* a cache under an unchanged key, while GHA caches are immutable — once written, a key never changes. So a static key like `key: build-cache` silently stops updating on GHA. Always fold a content hash into the key. `policy: pull` maps to actions/cache/restore and `policy: push` to actions/cache/save.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/cache.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
