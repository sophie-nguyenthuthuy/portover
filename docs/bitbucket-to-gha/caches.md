# Migrate Bitbucket Pipelines caches to GitHub Actions

**Directive:** `caches: [node, pip, custom-name]`

Part of the [bitbucket-to-gha](index.md) migration — `portover run bitbucket-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — bitbucket-pipelines.yml (Bitbucket Pipelines)

```yaml
caches:
  - node
  - pip
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
- uses: actions/cache@v4
  with:
    path: node_modules
    key: ${{ runner.os }}-node-${{ hashFiles('**/package-lock.json') }}
```

## What to watch for

Bitbucket ships named caches that already know their path (node, pip, maven, gradle...); GHA has no such registry, so portover expands each name into the path and a lockfile-hashed key. The difference to watch is invalidation: a Bitbucket cache is keyed by name and silently refreshed roughly weekly, while a GHA cache key is immutable — which is why the generated keys hash a lockfile. Check that the hashed file is the right one for your project. The `docker` cache has no equivalent; use docker/build-push-action's gha cache backend instead.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/caches.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
