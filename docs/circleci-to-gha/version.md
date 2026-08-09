# Migrate the CircleCI config version key to GitHub Actions

**Directive:** `version: 2.1`

Part of the [circleci-to-gha](index.md) migration — `portover run circleci-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .circleci/config.yml (CircleCI)

```yaml
version: 2.1
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
# nothing — GitHub Actions has no config version key
```

## What to watch for

GHA versions the actions you call (actions/checkout@v4), not the workflow format, so this key simply disappears. It does tell portover what to expect: 2.1 configs may use orbs, commands, executors and parameters, while 2.0 configs often have no `workflows:` block at all.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/version.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
