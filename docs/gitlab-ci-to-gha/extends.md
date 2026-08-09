# Migrate GitLab CI extends to GitHub Actions

**Directive:** `extends: .template`

Part of the [gitlab-ci-to-gha](index.md) migration — `portover run gitlab-ci-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .gitlab-ci.yml (GitLab CI)

```yaml
.tests:
  image: python:3.12
  before_script:
    - pip install -r requirements.txt

unit:
  extends: .tests
  script:
    - pytest -q
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
jobs:
  unit:
    container: python:3.12       # merged in from .tests
    steps:
      - uses: actions/checkout@v4
      - run: pip install -r requirements.txt
      - run: pytest -q
```

## What to watch for

GHA jobs cannot inherit from each other, so portover merges the template into the job at conversion time. The merge follows GitLab's rule: mappings merge key-by-key (so a job can override just `image:` inside a shared block) while lists and scalars replace outright. Multiple parents are merged left to right, and a parent may itself extend another. If you want to keep the reuse rather than the flattening, the GHA equivalents are a reusable workflow (`on: workflow_call`) or a composite action.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/extends.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
