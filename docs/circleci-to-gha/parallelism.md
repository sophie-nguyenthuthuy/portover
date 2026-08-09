# Migrate CircleCI job parallelism

**Directive:** `parallelism: N`

Part of the [circleci-to-gha](index.md) migration — `portover run circleci-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .circleci/config.yml (CircleCI)

```yaml
parallelism: 4
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
strategy:
  matrix:
    circle_node_index: [0, 1, 2, 3]
env:
  CIRCLE_NODE_INDEX: ${{ matrix.circle_node_index }}
```

## What to watch for

The fan-out is preserved, but CircleCI timing-based test splitting must be replaced with a test-runner sharding feature.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/parallelism.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
