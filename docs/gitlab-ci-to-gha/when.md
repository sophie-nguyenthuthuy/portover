# Migrate GitLab CI when to GitHub Actions

**Directive:** `when: manual / always / on_failure / delayed`

Part of the [gitlab-ci-to-gha](index.md) migration — `portover run gitlab-ci-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .gitlab-ci.yml (GitLab CI)

```yaml
cleanup:
  when: always

deploy:
  when: manual
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
cleanup:
  if: always()

deploy:
  # gated by an environment with required reviewers,
  # or triggered from on: workflow_dispatch
```

## What to watch for

`always` and `on_failure` are `if: always()` and `if: failure()`. `manual` is the interesting one: GitLab puts a play button on the job inside an otherwise-automatic pipeline, which GHA has no per-job equivalent for. The two honest options are an environment with required reviewers (the job runs but waits for approval) or a separate workflow_dispatch trigger. `delayed` with `start_in:` has no equivalent at all — the closest is a sleep step or a scheduled workflow.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/when.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
