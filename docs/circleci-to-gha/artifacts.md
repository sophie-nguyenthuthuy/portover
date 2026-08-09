# Migrate CircleCI artifacts and test results

**Directive:** `- store_artifacts / store_test_results`

Part of the [circleci-to-gha](index.md) migration — `portover run circleci-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .circleci/config.yml (CircleCI)

```yaml
- store_artifacts:
    path: coverage
- store_test_results:
    path: test-results
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
- uses: actions/upload-artifact@v4
  with:
    name: coverage
    path: coverage
```

## What to watch for

GHA stores test results as ordinary artifacts; add a reporting action if you want annotations and a test summary.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/artifacts.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
