# Migrate GitLab CI coverage regex to GitHub Actions

**Directive:** `coverage: /regex/`

Part of the [gitlab-ci-to-gha](index.md) migration — `portover run gitlab-ci-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .gitlab-ci.yml (GitLab CI)

```yaml
coverage: '/TOTAL.*\s+(\d+%)$/'
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
# no built-in coverage parsing; either:
- run: pytest --cov --cov-report=xml
- uses: irongut/CodeCoverageSummary@v1.3.0
  with:
    filename: coverage.xml
```

## What to watch for

GitLab scrapes the job log with this regex and shows the number on the MR and in badges. GHA has no log-scraping equivalent, so coverage moves to a report file plus an action (or a service like Codecov). The practical consequence is that the regex is dead weight — what you need instead is a `--cov-report=xml`-style flag on the test command.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/coverage.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
