# Migrate GitLab CI stages to GitHub Actions needs

**Directive:** `stages: [build, test, deploy]`

Part of the [gitlab-ci-to-gha](index.md) migration — `portover run gitlab-ci-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .gitlab-ci.yml (GitLab CI)

```yaml
stages:
  - build
  - test
  - deploy

unit:
  stage: test
lint:
  stage: test
ship:
  stage: deploy
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
jobs:
  unit:
    needs: build-job     # every job in the previous stage
  lint:
    needs: build-job
  ship:
    needs: [unit, lint]  # waits for the whole test stage
```

## What to watch for

GHA has no stages — only per-job `needs:`. The translation is mechanical but inverted: GitLab declares the *sequence* globally and gets parallelism for free within a stage, while GHA gets parallelism for free and you declare the sequence per job. portover wires each job to every job of the previous non-empty stage, which preserves the ordering exactly. A job with its own `needs:` keeps it — that's already a DAG. GitLab's implicit `.pre`/`.post` stages are not in the default list; declare them if you use them.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/stages.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
