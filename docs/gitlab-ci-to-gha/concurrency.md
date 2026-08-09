# Migrate GitLab CI interruptible and resource_group to GitHub Actions

**Directive:** `interruptible: true / resource_group: production`

Part of the [gitlab-ci-to-gha](index.md) migration — `portover run gitlab-ci-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .gitlab-ci.yml (GitLab CI)

```yaml
interruptible: true
resource_group: production
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true      # interruptible

# resource_group (never two at once, no cancelling):
concurrency:
  group: production
  cancel-in-progress: false
```

## What to watch for

Both GitLab directives land on GHA's single `concurrency` key, but they mean opposite things and portover keeps them apart: `interruptible` cancels a superseded run (cancel-in-progress: true), while `resource_group` serialises runs so a deploy is never concurrent with another (cancel-in-progress: false). Because portover writes concurrency at the workflow level, a resource_group on one job serialises the whole workflow — move it to that job's own `concurrency:` block if that is too broad.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/concurrency.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
