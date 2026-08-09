# Migrate Buildkite depends_on to GitHub Actions needs

**Directive:** `depends_on: key / [{step, allow_failure}]`

Part of the [buildkite-to-gha](index.md) migration — `portover run buildkite-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — Buildkite pipeline.yml

```yaml
- label: Deploy
  depends_on:
    - build
    - step: test
      allow_failure: true
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
deploy:
  needs: [build, test]
  if: always() && needs.build.result == 'success'
```

## What to watch for

`depends_on` references step `key:`s and maps onto `needs:` almost exactly — and in both systems, declaring it opts the step out of the implicit ordering (Buildkite's wait barriers, which portover would otherwise apply). The difference is failure handling: `allow_failure: true` lets the step run even if that dependency failed, which in GHA needs `if: always()` plus explicit result checks on the dependencies you still require, because a job with `needs:` is skipped by default when any dependency fails. Depending on a GROUP key expands to every job in that group, since GHA cannot depend on a set.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/depends_on.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
