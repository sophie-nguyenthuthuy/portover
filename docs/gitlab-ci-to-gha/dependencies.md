# Migrate GitLab CI dependencies to GitHub Actions

**Directive:** `dependencies: [build]`

Part of the [gitlab-ci-to-gha](index.md) migration — `portover run gitlab-ci-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .gitlab-ci.yml (GitLab CI)

```yaml
dependencies:
  - build
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
- uses: actions/download-artifact@v4
  with:
    name: build
```

## What to watch for

This is the directive people forget, and the resulting failure is confusing. GitLab passes artifacts from earlier stages *automatically*; `dependencies:` only narrows that set. GHA passes nothing between jobs — they run on different machines with fresh workspaces — so every artifact must be uploaded by the producer and downloaded by the consumer. portover adds the download step here, but a job that relied on the implicit pass-through (no `dependencies:` key at all) will need one added by hand. `dependencies: []` means 'download nothing', which is already the GHA default.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/dependencies.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
