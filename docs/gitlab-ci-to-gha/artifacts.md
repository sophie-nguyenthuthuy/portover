# Migrate GitLab CI artifacts to GitHub Actions

**Directive:** `artifacts: paths / reports / expire_in / when`

Part of the [gitlab-ci-to-gha](index.md) migration — `portover run gitlab-ci-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .gitlab-ci.yml (GitLab CI)

```yaml
artifacts:
  paths:
    - dist/
  reports:
    junit: report.xml
  expire_in: 1 week
  when: always
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
- uses: actions/upload-artifact@v4
  if: always()
  with:
    name: dist
    path: dist/
    retention-days: 7
```

## What to watch for

`paths` becomes upload-artifact and `expire_in` becomes retention-days. The real difference is `reports:` — GitLab parses those files and renders test results, coverage and security findings in the MR. GHA has no built-in report parsing: junit needs a reporter action (dorny/test-reporter), coverage needs a coverage action or a third-party service, and the security reports map to GitHub Advanced Security features rather than a file upload. portover uploads them as plain artifacts so nothing is lost, and flags each one.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/artifacts.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
