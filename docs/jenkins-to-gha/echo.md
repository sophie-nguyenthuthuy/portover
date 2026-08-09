# Migrate Jenkins echo steps to GitHub Actions

**Directive:** `echo 'message'`

Part of the [jenkins-to-gha](index.md) migration — `portover run jenkins-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — Jenkinsfile (declarative pipeline)

```groovy
echo 'Deploying to staging'
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
- run: echo "Deploying to staging"
```

## What to watch for

Groovy ${VAR} interpolation inside the message must become ${{ env.VAR }} or shell $VAR.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/echo.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
