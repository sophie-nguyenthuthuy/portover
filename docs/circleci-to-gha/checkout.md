# Migrate the CircleCI checkout step

**Directive:** `- checkout`

Part of the [circleci-to-gha](index.md) migration — `portover run circleci-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .circleci/config.yml (CircleCI)

```yaml
steps:
  - checkout
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
steps:
  - uses: actions/checkout@v4
```

## What to watch for

A non-default CircleCI checkout path is carried to actions/checkout's `path` input.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/checkout.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
