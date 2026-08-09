# Migrate CircleCI job parameters

**Directive:** `jobs.<job>.parameters`

Part of the [circleci-to-gha](index.md) migration — `portover run circleci-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .circleci/config.yml (CircleCI)

```yaml
parameters:
  python:
    type: string
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
strategy:
  matrix:
    python: ["3.11", "3.12"]
```

## What to watch for

The CircleCI workflow call site supplies matrix parameter values. References inside commands become `${{ matrix.<name> }}`. A job used without a matrix may need its defaults written directly into the workflow.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/job_parameters.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
