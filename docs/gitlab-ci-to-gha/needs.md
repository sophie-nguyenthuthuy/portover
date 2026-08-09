# Migrate GitLab CI needs to GitHub Actions

**Directive:** `needs: [job] / needs: [{job, artifacts, optional}]`

Part of the [gitlab-ci-to-gha](index.md) migration — `portover run gitlab-ci-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .gitlab-ci.yml (GitLab CI)

```yaml
needs:
  - build
  - job: lint
    artifacts: false
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
needs: [build, lint]
```

## What to watch for

The one GitLab directive that maps to GHA exactly — both are a job DAG, and declaring `needs:` overrides the stage order in both systems. Two details do not carry: `artifacts: false` (GHA never passes artifacts implicitly, so the flag is meaningless — you download what you want), and `optional: true` (GHA has no optional dependency; the job simply cannot depend on something that might not exist). `needs: []` means 'start immediately' in both.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/needs.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
