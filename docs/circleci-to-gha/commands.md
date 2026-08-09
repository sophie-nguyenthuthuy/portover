# Migrate CircleCI reusable commands to GitHub Actions

**Directive:** `commands: (reusable commands)`

Part of the [circleci-to-gha](index.md) migration — `portover run circleci-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .circleci/config.yml (CircleCI)

```yaml
commands:
  install_deps:
    steps:
      - run: pip install -r requirements.txt

jobs:
  test:
    steps:
      - install_deps
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
jobs:
  test:
    steps:
      - run: pip install -r requirements.txt   # inlined from install_deps
```

## What to watch for

GHA's equivalent is a composite action, which must live in its own directory with an action.yml — so portover inlines the command's steps at each call site instead, which is correct and keeps the workflow self-contained. If a command is called from many jobs and you'd rather share it, move those steps into .github/actions/<name>/action.yml and call it with `uses: ./.github/actions/<name>`. Command parameters (`<< parameters.x >>`) become matrix references when inlined — check them if the command took arguments.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/commands.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
