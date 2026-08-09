# Migrate Woodpecker workflow settings to GitHub Actions

**Directive:** `clone / skip_clone / labels / platform / runs_on / variables`

Part of the [woodpecker-to-gha](index.md) migration — `portover run woodpecker-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .woodpecker.yml (Woodpecker CI)

```yaml
labels:
  platform: linux/amd64

clone:
  git:
    image: woodpeckerci/plugin-git
    settings:
      depth: 50

runs_on: [success, failure]
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
runs-on: ubuntu-latest
steps:
  - uses: actions/checkout@v4
    with:
      fetch-depth: 50
# runs_on: [success, failure] -> if: always()
```

## What to watch for

`labels:` selects an agent by tag; `platform: linux/amd64` maps to a GitHub-hosted runner, while other labels mean self-hosted runners carrying the same labels. The `clone:` block customises the built-in git step, and its `depth:` is `fetch-depth:` (`skip_clone: true` means no checkout at all). `runs_on:` is easy to misread — it is not runner selection but the set of upstream STATUSES this workflow runs for, so listing failure means `if: always()`. `variables:` is a holding area for YAML anchors, which portover's reader refuses rather than guessing at; expand them first.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/workflow_settings.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
