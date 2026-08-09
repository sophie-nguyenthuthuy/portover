# Migrate Jenkins stages to GitHub Actions jobs

**Directive:** `stages { stage('X') { steps { ... } } }`

Part of the [jenkins-to-gha](index.md) migration — `portover run jenkins-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — Jenkinsfile (declarative pipeline)

```groovy
stages {
  stage('Build') { steps { sh 'make build' } }
  stage('Test')  { steps { sh 'make test' } }
}
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: make build
  test:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: make test
```

## What to watch for

Each stage becomes a job chained with needs: to keep Jenkins' sequential order. Jenkins stages share a workspace; GHA jobs do NOT — hand artifacts between jobs with upload-/download-artifact, or merge trivially-small stages into one job's steps. Declarative pipelines check out code implicitly, so every job starts with actions/checkout.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/stages.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
