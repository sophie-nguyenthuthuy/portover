# Migrate Buildkite block and input steps to GitHub Actions

**Directive:** `- block: / - input: with fields / prompt`

Part of the [buildkite-to-gha](index.md) migration — `portover run buildkite-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — Buildkite pipeline.yml

```yaml
- block: ":rocket: Release?"
  key: gate
  prompt: Ship to production?
  fields:
    - select: Environment
      key: env
      options:
        - {label: Staging, value: staging}
        - {label: Production, value: production}
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
gate:
  environment: approval      # add required reviewers in repo settings
  steps:
    - run: echo "approval gate"
# the fields have no in-run equivalent — collect them as
# workflow_dispatch inputs instead:
on:
  workflow_dispatch:
    inputs:
      env:
        type: choice
        options: [staging, production]
```

## What to watch for

A block step pauses a running build until someone clicks, and GHA's equivalent is an Environment with required reviewers — same effect, configured in repository settings rather than YAML. Where the two genuinely part ways is `fields:`: Buildkite collects input DURING the run and later steps read it with `buildkite-agent meta-data get`, while GHA can only take inputs BEFORE the run starts (workflow_dispatch). So a block step with fields has to be restructured — usually into a manually triggered workflow — and portover reports the fields it found so you can transplant them.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/block_input.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
