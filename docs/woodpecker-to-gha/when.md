# Migrate Woodpecker when conditions to GitHub Actions if

**Directive:** `when: [{event, branch, path, evaluate}]`

Part of the [woodpecker-to-gha](index.md) migration — `portover run woodpecker-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .woodpecker.yml (Woodpecker CI)

```yaml
when:
  - event: push
    branch: main
  - event: tag
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
if: (github.event_name == 'push' && github.ref_name == 'main') || github.ref_type == 'tag'
```

## What to watch for

This is the shape that differs most from Drone: Woodpecker's `when:` is a LIST of condition sets, and the sets are OR'd while the keys inside one set are AND'd — so the example runs on pushes to main and on any tag. portover reproduces that grouping exactly. (The single-map form is still accepted and behaves as one set.) `status: [success, failure]` becomes `always()` and is placed first, since a GHA step otherwise skips after a failure. `evaluate:` holds a CEL expression over Woodpecker's own variables and has no mechanical translation, so it is reported with its source text.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/when.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
