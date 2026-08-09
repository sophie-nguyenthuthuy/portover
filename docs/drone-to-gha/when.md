# Migrate Drone when conditions to GitHub Actions if

**Directive:** `when: branch / event / status / ref / path`

Part of the [drone-to-gha](index.md) migration — `portover run drone-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .drone.yml (Drone CI)

```yaml
when:
  branch:
    - main
  event:
    - push
  status:
    - success
    - failure
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
if: always() && github.ref_name == 'main' && github.event_name == 'push'
```

## What to watch for

Each condition type becomes part of one `if:` expression. The one that changes meaning is `status:` — listing both success and failure is Drone's way of saying 'run even if an earlier step failed', which is `always()` in GHA (and must come FIRST in the expression, since a GHA step otherwise skips after a failure). `event:` values map onto event names, with `tag` becoming a ref-type check. The exclude form (`branch: {exclude: [main]}`) becomes a negation. `path:` filters have no per-step equivalent — GHA path filters are workflow-level — so those are flagged with the dorny/paths-filter alternative.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/when.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
