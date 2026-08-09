# Migrate a CircleCI Docker executor to GitHub Actions

**Directive:** `docker: [{image, environment, auth}]`

Part of the [circleci-to-gha](index.md) migration — `portover run circleci-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .circleci/config.yml (CircleCI)

```yaml
docker:
  - image: cimg/python:3.12
    environment:
      PIP_DISABLE_PIP_VERSION_CHECK: "1"
  - image: postgres:16
    environment:
      POSTGRES_PASSWORD: postgres
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
container: cimg/python:3.12
env:
  PIP_DISABLE_PIP_VERSION_CHECK: "1"
services:
  service-1:
    image: postgres:16
    env:
      POSTGRES_PASSWORD: postgres
```

## What to watch for

The first CircleCI image is the primary container; later images become GHA service containers. CircleCI image aliases and service readiness checks do not translate exactly, so portover flags aliases and custom entrypoints.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/docker.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
