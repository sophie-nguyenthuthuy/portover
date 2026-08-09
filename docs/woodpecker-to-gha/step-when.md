# Migrate Woodpecker per-step when conditions to GitHub Actions

**Directive:** `when: (on a step)`

Part of the [woodpecker-to-gha](index.md) migration — `portover run woodpecker-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .woodpecker.yml (Woodpecker CI)

```yaml
- name: notify
  image: alpine
  when:
    - status: [success, failure]
  commands: [./notify.sh]
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
- name: notify
  if: always()
  run: ./notify.sh
```

## What to watch for

The same condition-set grammar as a workflow-level `when:`, applied to one step. The difference in effect is worth noting: a step condition becomes an `if:` on a GHA STEP, and unlike the workflow level it cannot add triggers — a step cannot make the workflow run for an event the workflow was not triggered for. So a step whose `when:` names an event outside the workflow's own triggers will simply never fire; check the workflow-level `on:` if a step goes quiet after migrating.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/step_when.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
