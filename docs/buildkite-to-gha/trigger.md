# Migrate Buildkite trigger steps to GitHub Actions

**Directive:** `- trigger: other-pipeline / build / async`

Part of the [buildkite-to-gha](index.md) migration — `portover run buildkite-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — Buildkite pipeline.yml

```yaml
- trigger: deploy-pipeline
  label: Deploy
  async: false
  build:
    branch: main
    env:
      RELEASE: "true"
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
deploy:
  uses: ./.github/workflows/deploy.yml
  with:
    RELEASE: "true"
  secrets: inherit
```

## What to watch for

A trigger step becomes a reusable-workflow call, and the job then uses `uses:` INSTEAD of `runs-on`/`steps` — the called workflow must declare `on: workflow_call`. The `async:` flag decides which shape fits: `async: false` (wait for the triggered build) is exactly a workflow call, while `async: true` (fire and forget) has no calling equivalent and is closer to `repository_dispatch` with a token. `build.env` becomes the called workflow's `with:` inputs, which must be declared there — environment variables do not cross the boundary on their own.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/trigger.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
