# Migrate Azure Pipelines pool to GitHub Actions runs-on

**Directive:** `pool: vmImage / name / demands`

Part of the [azure-pipelines-to-gha](index.md) migration — `portover run azure-pipelines-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — azure-pipelines.yml (Azure Pipelines)

```yaml
pool:
  vmImage: ubuntu-latest
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
runs-on: ubuntu-latest
```

## What to watch for

Microsoft-hosted `vmImage` values map almost one-to-one, including the older names (ubuntu-20.04, windows-2019, macOS-latest -> macos-latest). A `name:` pool instead of a vmImage means a self-hosted agent pool, which becomes a self-hosted runner label; `demands:` (capability matching) has no GHA equivalent beyond adding more labels. A top-level pool applies to every job unless the job sets its own.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/pool.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
