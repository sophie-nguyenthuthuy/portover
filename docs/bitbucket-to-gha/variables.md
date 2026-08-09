# Migrate Bitbucket Pipelines variables to GitHub Actions

**Directive:** `$BITBUCKET_COMMIT, $BITBUCKET_BRANCH, $BITBUCKET_BUILD_NUMBER, ...`

Part of the [bitbucket-to-gha](index.md) migration — `portover run bitbucket-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — bitbucket-pipelines.yml (Bitbucket Pipelines)

```yaml
script:
  - docker build -t app:$BITBUCKET_COMMIT .
  - echo "on branch $BITBUCKET_BRANCH build $BITBUCKET_BUILD_NUMBER"
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
env:   # added automatically, so the scripts keep working unchanged
  BITBUCKET_COMMIT: ${{ github.sha }}
  BITBUCKET_BRANCH: ${{ github.ref_name }}
  BITBUCKET_BUILD_NUMBER: ${{ github.run_number }}
```

## What to watch for

Bitbucket variables are plain shell variables, so rather than editing every command (and risking a bad edit inside a quoted string), portover defines the ones your scripts actually use as workflow-level `env:` sourced from the github context. The scripts migrate byte-for-byte. Only referenced variables are defined. Two have no faithful equivalent and are flagged: $BITBUCKET_COMMIT is a full SHA while some scripts expect Bitbucket's shortened form, and $BITBUCKET_REPO_OWNER-style identity variables differ. Repository variables you set in Bitbucket's UI are not in this file at all — recreate them as GitHub secrets.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/variables.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
