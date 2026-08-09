# Migrate GitLab CI global variables to GitHub Actions env

**Directive:** `variables: (global)`

Part of the [gitlab-ci-to-gha](index.md) migration — `portover run gitlab-ci-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .gitlab-ci.yml (GitLab CI)

```yaml
variables:
  APP_ENV: production
  PIP_CACHE_DIR: .cache/pip
  DEPLOY_TOKEN:
    description: set at pipeline run time
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
env:
  APP_ENV: production
  PIP_CACHE_DIR: .cache/pip
```

## What to watch for

Plain values map to a workflow-level `env:` block. Two things do not carry over: masked/protected CI/CD variables set in the GitLab UI have no YAML representation at all — recreate them as repository secrets and reference `${{ secrets.NAME }}`; and a variable declared with a `description:` is a run-time input in GitLab, which is a workflow_dispatch input in GHA.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/variables.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
