# Migrate Jenkins artifact steps to GitHub Actions

**Directive:** `archiveArtifacts / junit / stash / unstash`

Part of the [jenkins-to-gha](index.md) migration — `portover run jenkins-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — Jenkinsfile (declarative pipeline)

```groovy
archiveArtifacts artifacts: 'dist/**'
junit 'reports/**/*.xml'
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
- uses: actions/upload-artifact@v4
  with: { name: dist, path: dist/** }
- uses: actions/upload-artifact@v4
  if: always()
  with: { name: test-reports, path: reports/**/*.xml }
```

## What to watch for

junit has no built-in equivalent — reports are uploaded as artifacts; add a marketplace reporter (e.g. dorny/test-reporter) for annotations. stash/unstash between stages becomes upload-artifact in one job and download-artifact in the job that needs: it.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/artifacts.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
