# Migrate GitLab CI environment to GitHub Actions

**Directive:** `environment: name / url / on_stop`

Part of the [gitlab-ci-to-gha](index.md) migration — `portover run gitlab-ci-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .gitlab-ci.yml (GitLab CI)

```yaml
environment:
  name: production
  url: https://example.com
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
environment:
  name: production
  url: https://example.com
```

## What to watch for

Nearly identical — both track deployments per named environment and both show the URL. GHA environments additionally carry protection rules (required reviewers, wait timers, branch restrictions) and environment-scoped secrets, which is where GitLab's `when: manual` deploy gate ends up. `on_stop`/`auto_stop_in` (GitLab's dynamic environment teardown) have no equivalent: write an explicit cleanup job. Dynamic names like `review/$CI_COMMIT_REF_NAME` work, but the variable must be a GHA expression.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/environment.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
