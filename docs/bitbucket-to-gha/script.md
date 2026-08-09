# Migrate Bitbucket Pipelines script to GitHub Actions run steps

**Directive:** `script / after-script`

Part of the [bitbucket-to-gha](index.md) migration — `portover run bitbucket-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — bitbucket-pipelines.yml (Bitbucket Pipelines)

```yaml
script:
  - npm ci
  - npm test
after-script:
  - ./report.sh
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
steps:
  - uses: actions/checkout@v4
  - run: npm ci
  - run: npm test
  - if: always()
    run: ./report.sh
```

## What to watch for

Each command becomes its own `run:` step, so a failure points at one line the way Bitbucket's log does. `after-script` runs even when the step failed, which is `if: always()`. One behaviour worth knowing: in Bitbucket, `after-script` can read $BITBUCKET_EXIT_CODE to tell success from failure — in GHA you would branch on `${{ job.status }}` or split into `if: success()` / `if: failure()` steps instead.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/script.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
