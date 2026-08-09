# Migrate Jenkins when conditions to GitHub Actions if:

**Directive:** `when { branch / tag / changeRequest / environment / expression }`

Part of the [jenkins-to-gha](index.md) migration — `portover run jenkins-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — Jenkinsfile (declarative pipeline)

```groovy
when { branch 'main' }
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
if: github.ref == 'refs/heads/main'
```

## What to watch for

branch -> github.ref, tag -> startsWith(github.ref, 'refs/tags/'), changeRequest() -> github.event_name == 'pull_request', environment name/value -> env comparison. `expression { }` is Groovy — rewrite the logic in GHA expression syntax by hand (flagged).

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/when.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
