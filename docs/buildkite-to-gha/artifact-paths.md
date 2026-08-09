# Migrate Buildkite artifact_paths to GitHub Actions

**Directive:** `artifact_paths: dist/**`

Part of the [buildkite-to-gha](index.md) migration — `portover run buildkite-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — Buildkite pipeline.yml

```yaml
- label: Build
  command: make build
  artifact_paths:
    - dist/**
    - coverage/*.xml
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
- uses: actions/upload-artifact@v4
  if: always()
  with:
    name: build
    path: |
      dist/**
      coverage/*.xml
```

## What to watch for

Buildkite uploads these even when the step fails (which is the point for logs and coverage), so portover adds `if: always()` to match — without it a GHA step is skipped after a failure and you lose exactly the artifacts you wanted. Downloading is the other half: Buildkite steps pull artifacts with `buildkite-agent artifact download`, while GHA needs an explicit actions/download-artifact in the consuming job.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/artifact_paths.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
