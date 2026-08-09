# Migrate Jenkins checkout scm to GitHub Actions

**Directive:** `checkout scm`

Part of the [jenkins-to-gha](index.md) migration — `portover run jenkins-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — Jenkinsfile (declarative pipeline)

```groovy
checkout scm
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
- uses: actions/checkout@v4
```

## What to watch for

portover already prepends actions/checkout to every job (declarative pipelines check out implicitly), so an explicit `checkout scm` is dropped rather than duplicated. deleteDir/cleanWs are no-ops: every GHA job starts on a fresh workspace.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/checkout.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
