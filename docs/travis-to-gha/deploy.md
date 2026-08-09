# Migrate Travis deploy to GitHub Actions

**Directive:** `deploy: provider: pypi / pages / script / releases ...`

Part of the [travis-to-gha](index.md) migration — `portover run travis-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .travis.yml (Travis CI)

```yaml
deploy:
  provider: pypi
  username: __token__
  on:
    tags: true
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
# separate job, gated on tags:
publish:
  if: startsWith(github.ref, 'refs/tags/')
  permissions: { id-token: write }
  steps:
    - uses: pypa/gh-action-pypi-publish@release/v1
```

## What to watch for

Deployment is where 1:1 translation stops being a favor — each provider has a better native pattern: pypi -> trusted publishing (no token at all), pages -> actions/deploy-pages, releases -> softprops/action-gh-release, script -> a run step gated with `if: startsWith(github.ref, 'refs/tags/')`. portover flags the provider and points at the pattern instead of transplanting credentials.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/deploy.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
