# Migrate Bitbucket Pipelines sections to GitHub Actions workflows

**Directive:** `pipelines: default / branches / tags / pull-requests / custom`

Part of the [bitbucket-to-gha](index.md) migration — `portover run bitbucket-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — bitbucket-pipelines.yml (Bitbucket Pipelines)

```yaml
pipelines:
  default:
    - step:
        name: Build
        script: [make build]
    - step:
        name: Test
        script: [make test]
  branches:
    main:
      - step:
          script: [./deploy.sh]
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
# .github/workflows/default.yml
on: {push: {}}
jobs:
  build:
    steps: [...]
  test:
    needs: build      # steps are sequential in Bitbucket
    steps: [...]

# .github/workflows/branches-main.yml
on: {push: {branches: [main]}}
```

## What to watch for

Each section is triggered differently, and GHA scopes triggers per FILE, so each becomes its own workflow. `default` is every push that no `branches:` pattern claims — GHA has no 'everything else' trigger, so portover emits a plain `on: push` and flags it when specific branch pipelines exist alongside it. `custom:` pipelines are manual, which is `workflow_dispatch` (their `variables:` become inputs). Within a section, steps run one after another, so they are chained with `needs:` — and because Bitbucket hands each step the artifacts of every earlier step automatically, portover inserts the matching download-artifact steps that GHA requires.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/pipelines.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
