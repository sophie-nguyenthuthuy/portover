# Migrate CircleCI job environment variables

**Directive:** `jobs.<job>.environment`

Part of the [circleci-to-gha](index.md) migration — `portover run circleci-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .circleci/config.yml (CircleCI)

```yaml
environment:
  APP_ENV: test
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
env:
  APP_ENV: test
```

## What to watch for

Do not migrate secret values into YAML; replace them with `${{ secrets.NAME }}`.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/job_environment.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
