# Migrate Jenkins agent to GitHub Actions runs-on

**Directive:** `agent any / agent { label } / agent { docker }`

Part of the [jenkins-to-gha](index.md) migration — `portover run jenkins-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — Jenkinsfile (declarative pipeline)

```groovy
agent { docker { image 'python:3.12' } }
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    container: python:3.12
```

## What to watch for

`agent any` -> runs-on: ubuntu-latest. `label 'x'` -> runs-on: [self-hosted, x] (register your Jenkins nodes as self-hosted runners). `docker { image }` -> container:. `dockerfile` has no direct equivalent — build the image in a step or prebuild it to a registry.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/agent.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
