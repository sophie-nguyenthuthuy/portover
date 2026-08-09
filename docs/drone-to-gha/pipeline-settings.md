# Migrate Drone pipeline settings to GitHub Actions

**Directive:** `platform / clone / workspace / volumes / node / image_pull_secrets`

Part of the [drone-to-gha](index.md) migration — `portover run drone-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .drone.yml (Drone CI)

```yaml
platform:
  os: linux
  arch: amd64

clone:
  depth: 50

workspace:
  path: /drone/src
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
runs-on: ubuntu-latest
steps:
  - uses: actions/checkout@v4
    with:
      fetch-depth: 50
```

## What to watch for

`platform` picks the runner: linux/amd64 is ubuntu-latest, windows is windows-latest, darwin is macos-latest, and arm64 needs a self-hosted or ARM runner. `clone.depth` maps to `fetch-depth` (`clone.disable: true` means no checkout at all). `workspace.path` has no equivalent worth reproducing — GHA always checks out into ${{ github.workspace }}, and anything reading $DRONE_WORKSPACE should use that instead. `volumes`, `node` (agent labels) and `image_pull_secrets` describe the Drone runner fleet and are flagged.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/pipeline_settings.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
