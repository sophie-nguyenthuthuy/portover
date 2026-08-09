# Migrate GitLab CI job variables to GitHub Actions

**Directive:** `<job>.variables`

Part of the [gitlab-ci-to-gha](index.md) migration — `portover run gitlab-ci-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .gitlab-ci.yml (GitLab CI)

```yaml
deploy:
  variables:
    APP_ENV: production
    DEPLOY_KEY: $PROD_DEPLOY_KEY
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
deploy:
  env:
    APP_ENV: production
    DEPLOY_KEY: ${{ secrets.PROD_DEPLOY_KEY }}
```

## What to watch for

Job variables become the job's `env:` and override the workflow-level block, same precedence as GitLab. A value that just forwards another variable (`$PROD_DEPLOY_KEY`) is almost always a masked CI/CD variable from the GitLab UI — portover rewrites those references to `${{ secrets.NAME }}` and flags them so you remember to create the secret.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/job_variables.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
