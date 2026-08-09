# Migrate GitLab CI script blocks to GitHub Actions run steps

**Directive:** `script / before_script / after_script`

Part of the [gitlab-ci-to-gha](index.md) migration — `portover run gitlab-ci-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .gitlab-ci.yml (GitLab CI)

```yaml
before_script:
  - pip install -r requirements.txt
script:
  - pytest -q
  - coverage report
after_script:
  - ./cleanup.sh
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
steps:
  - uses: actions/checkout@v4
  - run: pip install -r requirements.txt
  - run: pytest -q
  - run: coverage report
  - run: ./cleanup.sh
```

## What to watch for

Each command becomes its own `run:` step, so the log has the same shape as GitLab's and a failure points at one command. Two behaviours do not survive the move and are worth checking: `after_script` in GitLab runs even when the job fails (add `if: always()` to match), and it runs in a *fresh shell*, so shell state set earlier is gone — while in GHA every step shares the runner but not the shell either, so exported variables need `>> "$GITHUB_ENV"`.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/script.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
