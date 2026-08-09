# Migrate the remaining Bitbucket Pipelines step settings to GitHub Actions

**Directive:** `size / max-time / oidc / runs-on / fail-fast / condition`

Part of the [bitbucket-to-gha](index.md) migration — `portover run bitbucket-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — bitbucket-pipelines.yml (Bitbucket Pipelines)

```yaml
- step:
    size: 2x
    max-time: 30
    oidc: true
    runs-on: [self.hosted, linux]
    condition:
      changesets:
        includePaths: [src/**]
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
timeout-minutes: 30
permissions:
  id-token: write        # oidc: true
runs-on: [self-hosted, linux]
# condition.changesets -> dorny/paths-filter, or on: push: paths:
```

## What to watch for

`max-time` is `timeout-minutes` (note the defaults differ: Bitbucket caps a step at 120 minutes, GHA at 360). `oidc: true` becomes `permissions: id-token: write`, which is the same mechanism for keyless cloud auth. `size` (2x/4x/8x) buys a bigger container and maps to a larger runner label your org configures. `condition.changesets` is a per-step path filter; GHA path filters are per-workflow, so the per-job equivalent is dorny/paths-filter.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/step_settings.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
