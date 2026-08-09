# Migrate CircleCI jobs to GitHub Actions jobs

**Directive:** `jobs: <name>: steps: [...]`

Part of the [circleci-to-gha](index.md) migration — `portover run circleci-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .circleci/config.yml (CircleCI)

```yaml
jobs:
  test:
    docker:
      - image: cimg/python:3.12
    steps:
      - checkout
      - run: pytest -q
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    container: cimg/python:3.12
    steps:
      - uses: actions/checkout@v4
      - run: pytest -q
```

## What to watch for

A CircleCI job is only a definition — the `workflows:` block decides whether and when it runs. GHA jobs are both at once, so portover converts the definitions here and lets the workflows mapping emit them with needs/if attached. Job names are slugged to valid GHA job ids (`build-and-test`, not `build_and test`).

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/jobs.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
