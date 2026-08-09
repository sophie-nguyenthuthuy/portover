# Migrate Travis build phases to GitHub Actions steps

**Directive:** `before_install / install / script / after_success / after_failure ...`

Part of the [travis-to-gha](index.md) migration — `portover run travis-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .travis.yml (Travis CI)

```yaml
install:
  - pip install -r requirements.txt
script:
  - pytest -q
after_failure:
  - cat logs/test.log
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
steps:
  - run: pip install -r requirements.txt
  - run: pytest -q
  - if: failure()
    run: cat logs/test.log
```

## What to watch for

Phases flatten into ordered steps of one job. after_success -> `if: success()`, after_failure -> `if: failure()`, after_script -> `if: always()`. One Travis semantic does not carry: after_* results never affected the Travis build status, but a failing `if:` step DOES fail the GHA job — append `|| true` if you relied on that.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/scripts.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
