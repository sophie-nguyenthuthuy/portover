# Migrate Jenkins environment blocks to GitHub Actions env

**Directive:** `environment { KEY = 'value' }`

Part of the [jenkins-to-gha](index.md) migration — `portover run jenkins-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — Jenkinsfile (declarative pipeline)

```groovy
environment {
  REGISTRY = 'ghcr.io'
  API_TOKEN = credentials('api-token')
}
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
env:
  REGISTRY: ghcr.io
  API_TOKEN: ${{ secrets.API_TOKEN }}
```

## What to watch for

Plain assignments map 1:1. `credentials('id')` becomes a repository secret — create it under Settings > Secrets and variables > Actions. Jenkins usernamePassword credentials split into TWO secrets (_USR/_PSW).

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/environment.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
