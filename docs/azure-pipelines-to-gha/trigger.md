# Migrate Azure Pipelines trigger to GitHub Actions on push

**Directive:** `trigger: branches / tags / paths / none`

Part of the [azure-pipelines-to-gha](index.md) migration — `portover run azure-pipelines-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — azure-pipelines.yml (Azure Pipelines)

```yaml
trigger:
  branches:
    include: [main, release/*]
    exclude: [experimental/*]
  paths:
    include: [src/*]
  tags:
    include: ["v*"]
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
on:
  push:
    branches: [main, "release/*"]
    branches-ignore: [experimental/*]
    paths: [src/*]
    tags: ["v*"]
```

## What to watch for

include/exclude become branches/branches-ignore, and Azure's `*` wildcards are already GHA glob syntax. Two gotchas: `trigger: none` means no CI trigger at all (portover drops `on: push` rather than leaving a trigger that would fire unexpectedly), and the bare list form `trigger: [main]` is branch-only shorthand. Note GHA cannot put branches and branches-ignore on the same event — if your config uses both, portover keeps includes and flags the excludes.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/trigger.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
