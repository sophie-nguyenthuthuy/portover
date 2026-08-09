# Migrate Jenkins sh and bat steps to GitHub Actions run

**Directive:** `sh 'cmd' / bat 'cmd'`

Part of the [jenkins-to-gha](index.md) migration — `portover run jenkins-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — Jenkinsfile (declarative pipeline)

```groovy
sh 'make test'
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
- run: make test
```

## What to watch for

sh -> run (bash). bat -> run with shell: cmd — and the job must be on a windows-latest runner. sh(returnStdout: true) captured into a Groovy variable becomes `>> "$GITHUB_OUTPUT"` plumbing (flagged).

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/sh.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
