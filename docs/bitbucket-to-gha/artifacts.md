# Migrate Bitbucket Pipelines artifacts to GitHub Actions

**Directive:** `artifacts: [dist/**] / artifacts: {paths, download}`

Part of the [bitbucket-to-gha](index.md) migration — `portover run bitbucket-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — bitbucket-pipelines.yml (Bitbucket Pipelines)

```yaml
- step:
    name: Build
    script: [make build]
    artifacts:
      - dist/**
- step:
    name: Deploy
    script: [./deploy.sh]     # dist/ is simply there
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
build:
  steps:
    - run: make build
    - uses: actions/upload-artifact@v4
      with: {name: build, path: dist/**}
deploy:
  needs: build
  steps:
    - uses: actions/download-artifact@v4   # added: GHA never passes files on
      with: {name: build}
    - run: ./deploy.sh
```

## What to watch for

This is the difference that silently breaks migrated pipelines. Bitbucket gives every LATER step the artifacts of every earlier one, with no declaration at the consuming end — GHA jobs share nothing. So portover uploads at the producer and inserts the matching download-artifact in each subsequent job, reproducing the implicit behaviour. `download: false` on a step opts out of receiving them, which is the GHA default anyway.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/artifacts.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
