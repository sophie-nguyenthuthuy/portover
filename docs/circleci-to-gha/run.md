# Migrate a CircleCI run step

**Directive:** `- run: <command>`

Part of the [circleci-to-gha](index.md) migration — `portover run circleci-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .circleci/config.yml (CircleCI)

```yaml
- run:
    name: Unit tests
    command: pytest -q
    no_output_timeout: 20m
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
- name: Unit tests
  run: pytest -q
  timeout-minutes: 20
```

## What to watch for

CircleCI `when: always` becomes `if: always()`. Background processes and per-step environments need review.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/run.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
