# Migrate a CircleCI macOS executor

**Directive:** `macos: {xcode: ...}`

Part of the [circleci-to-gha](index.md) migration — `portover run circleci-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .circleci/config.yml (CircleCI)

```yaml
macos:
  xcode: 15.4.0
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
runs-on: macos-14
```

## What to watch for

Xcode is selected through the runner image on GHA; verify the current runner/Xcode table.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/macos.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
