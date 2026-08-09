# Migrate GitLab CI jobs to GitHub Actions jobs

**Directive:** `<job name>: (any top-level key that is not a pipeline setting)`

Part of the [gitlab-ci-to-gha](index.md) migration — `portover run gitlab-ci-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .gitlab-ci.yml (GitLab CI)

```yaml
unit tests:
  stage: test
  image: python:3.12
  script:
    - pytest -q

.template:          # hidden: a template, never runs
  before_script:
    - pip install -r requirements.txt
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
jobs:
  unit-tests:
    runs-on: ubuntu-latest
    container: python:3.12
    steps:
      - uses: actions/checkout@v4
      - run: pytest -q
```

## What to watch for

GitLab has no `jobs:` key — any top-level key that is not a pipeline setting IS a job, which is why portover claims them here last, after every other mapping has had its chance. Two conversions happen: job names are slugged into valid GHA job ids (`unit tests` -> `unit-tests`, with the original kept as the display `name:`), and jobs whose name starts with a dot are hidden templates — they are recorded for `extends:` and never emitted as jobs. Every job starts with actions/checkout, because GitLab clones the repo for you.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/jobs.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
