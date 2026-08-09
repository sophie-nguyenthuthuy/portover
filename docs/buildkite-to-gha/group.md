# Migrate Buildkite group steps to GitHub Actions

**Directive:** `- group: name / steps / depends_on`

Part of the [buildkite-to-gha](index.md) migration — `portover run buildkite-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — Buildkite pipeline.yml

```yaml
- group: ":test: Tests"
  key: tests
  depends_on: build
  steps:
    - label: Unit
      command: make unit
    - label: Lint
      command: make lint
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
jobs:
  unit:
    needs: build      # the group's depends_on, applied to each member
    steps: [...]
  lint:
    needs: build
    steps: [...]
```

## What to watch for

A group is presentation plus a shared dependency — GHA has no grouping construct, so portover flattens it and pushes the group's `depends_on` onto each member. The part that does not survive is the group KEY: other steps can `depends_on` a whole group in Buildkite, but a GHA job cannot depend on a set, so portover expands such a reference into every job the group contained.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/group.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
