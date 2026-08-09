# Migrate the GitLab CI default block to GitHub Actions

**Directive:** `default: / top-level image, services, before_script, after_script, cache`

Part of the [gitlab-ci-to-gha](index.md) migration — `portover run gitlab-ci-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .gitlab-ci.yml (GitLab CI)

```yaml
default:
  image: python:3.12
  before_script:
    - pip install -r requirements.txt
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
jobs:
  test:
    container: python:3.12
    steps:
      - uses: actions/checkout@v4
      - run: pip install -r requirements.txt   # copied into every job
      - run: pytest -q
```

## What to watch for

GHA has no pipeline-wide job defaults, so portover copies each default into every job it applies to — a job that sets its own `image:` or `before_script:` overrides it, exactly like GitLab. The one GHA default that does exist is `defaults.run` (shell and working-directory), which is per-workflow. Top-level `image:`/`services:`/`cache:`/`before_script:` are the older spelling of the same thing and are treated identically.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/defaults.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
