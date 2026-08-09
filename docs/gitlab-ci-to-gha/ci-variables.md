# Migrate GitLab CI predefined variables to GitHub Actions

**Directive:** `$CI_COMMIT_SHA, $CI_COMMIT_BRANCH, $CI_REGISTRY_IMAGE, ...`

Part of the [gitlab-ci-to-gha](index.md) migration — `portover run gitlab-ci-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .gitlab-ci.yml (GitLab CI)

```yaml
script:
  - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .
  - echo "built from $CI_COMMIT_BRANCH"
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
env:   # added automatically, so the scripts keep working unchanged
  CI: "true"
  CI_REGISTRY_IMAGE: ghcr.io/${{ github.repository }}
  CI_COMMIT_SHA: ${{ github.sha }}
  CI_COMMIT_BRANCH: ${{ github.ref_name }}
```

## What to watch for

Rather than rewriting every shell command (and risking a bad edit inside a quoted string), portover defines the GitLab variables your scripts actually use as workflow-level `env:` sourced from the github context. The scripts stay byte-for-byte identical and keep working. Only variables that are genuinely referenced get defined. A few have no faithful equivalent and are flagged instead: CI_COMMIT_SHORT_SHA (GHA expressions cannot truncate — use `$(git rev-parse --short HEAD)`), CI_JOB_TOKEN (GITHUB_TOKEN is scoped differently and cannot clone other private repos), and CI_PIPELINE_URL.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/ci_variables.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
