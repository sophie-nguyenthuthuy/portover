# Migrate Jenkins post blocks to GitHub Actions

**Directive:** `post { always / success / failure }`

Part of the [jenkins-to-gha](index.md) migration — `portover run jenkins-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — Jenkinsfile (declarative pipeline)

```groovy
post {
  always  { junit 'reports/**/*.xml' }
  failure { sh './notify.sh' }
}
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
jobs:
  post:
    needs: [build, test]
    if: always()
    steps:
      - if: ${{ contains(needs.*.result, 'failure') }}
        run: ./notify.sh
```

## What to watch for

A trailing job with `if: always()` and needs: on every other job. Inside it, success is `!contains(needs.*.result, 'failure')` and failure is `contains(needs.*.result, 'failure')` — job-level success()/failure() would refer to the post job itself.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/post.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
