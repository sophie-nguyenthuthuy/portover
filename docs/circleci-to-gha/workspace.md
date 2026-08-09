# Migrate CircleCI workspaces

**Directive:** `- persist_to_workspace / attach_workspace`

Part of the [circleci-to-gha](index.md) migration — `portover run circleci-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .circleci/config.yml (CircleCI)

```yaml
- persist_to_workspace:
    root: .
    paths: [dist]
- attach_workspace:
    at: .
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
- uses: actions/upload-artifact@v4
  with:
    name: workspace
    path: dist
- uses: actions/download-artifact@v4
  with:
    name: workspace
    path: .
```

## What to watch for

Artifacts are the closest GHA equivalent. Artifact paths are rooted differently, so verify the download layout.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/workspace.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
