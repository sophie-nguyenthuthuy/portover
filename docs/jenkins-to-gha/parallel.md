# Migrate Jenkins parallel stages to GitHub Actions jobs

**Directive:** `stage { parallel { stage ... stage ... } }`

Part of the [jenkins-to-gha](index.md) migration — `portover run jenkins-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — Jenkinsfile (declarative pipeline)

```groovy
stage('Test') {
  parallel {
    stage('unit') { steps { sh 'make unit' } }
    stage('lint') { steps { sh 'make lint' } }
  }
}
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
jobs:
  unit:
    needs: build
    steps: [ ... ]
  lint:
    needs: build
    steps: [ ... ]
  deploy:
    needs: [unit, lint]
```

## What to watch for

GHA jobs are parallel by default — the migration is inverted: Jenkins marks parallelism explicitly, GHA marks *sequencing* (needs:) explicitly. Sibling parallel stages share the same needs; the next sequential stage needs all of them. For matrix-shaped duplication, collapse the jobs into strategy.matrix by hand.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/parallel.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
