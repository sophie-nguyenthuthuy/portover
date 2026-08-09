# Migrate the CircleCI job shell

**Directive:** `shell: /bin/bash -eo pipefail`

Part of the [circleci-to-gha](index.md) migration — `portover run circleci-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .circleci/config.yml (CircleCI)

```yaml
shell: /bin/bash -eo pipefail
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
defaults:
  run:
    shell: bash
```

## What to watch for

GHA supplies its own failure flags. Complex CircleCI shell command lines are reduced to the executable and flagged.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/shell.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
