# Migrate Buildkite plugins to GitHub Actions

**Directive:** `plugins: [org/name#v1.0.0: {config}]`

Part of the [buildkite-to-gha](index.md) migration — `portover run buildkite-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — Buildkite pipeline.yml

```yaml
plugins:
  - docker#v5.10.0:
      image: python:3.12
  - artifacts#v1.9.0:
      upload: dist/**
  - ecr#v2.7.0:
      login: true
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
container: python:3.12          # docker plugin
steps:
  - uses: aws-actions/amazon-ecr-login@v2   # ecr plugin
  - uses: actions/upload-artifact@v4        # artifacts plugin
    with: {name: build, path: dist/**}
```

## What to watch for

Plugins are Buildkite's answer to actions, so the common ones have real counterparts and portover translates those: docker becomes the job's `container:`, artifacts becomes upload-/download-artifact, cache becomes actions/cache, ecr becomes amazon-ecr-login. The mismatch to watch is lifecycle — a Buildkite plugin can hook before AND after the command (docker-login logs in first, junit-annotate reports afterwards), while a GHA action is just a step in a sequence, so the ordering becomes explicit. Plugins with no equivalent become a visible TODO step rather than vanishing.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/plugins.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
