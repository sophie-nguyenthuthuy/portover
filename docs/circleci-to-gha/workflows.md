# Migrate CircleCI workflows to GitHub Actions

**Directive:** `workflows: <name>: jobs: [{job: {requires, filters, context}}]`

Part of the [circleci-to-gha](index.md) migration — `portover run circleci-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .circleci/config.yml (CircleCI)

```yaml
workflows:
  build_test_deploy:
    jobs:
      - build
      - test:
          requires: [build]
      - deploy:
          requires: [test]
          filters:
            branches:
              only: main
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
# .github/workflows/build_test_deploy.yml
jobs:
  build: { ... }
  test:
    needs: build
    ...
  deploy:
    needs: test
    if: github.ref == 'refs/heads/main'
    ...
```

## What to watch for

One CircleCI workflow becomes one workflow FILE, because GHA scopes triggers per file rather than per job. `requires` maps to `needs`. Filters are the sharp edge: they are per-job in CircleCI but per-file in GHA, so portover keeps them as job-level `if:` conditions — and when any job filters on tags it also adds `on: push: tags:`, because an `if:` alone can never fire on a tag the workflow was not triggered for. `type: approval` jobs become a GHA environment with required reviewers (configured in repo settings, not YAML).

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/workflows.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
