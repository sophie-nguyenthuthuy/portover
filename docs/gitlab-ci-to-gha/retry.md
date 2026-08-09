# Migrate GitLab CI retry to GitHub Actions

**Directive:** `retry: 2 / retry: {max, when}`

Part of the [gitlab-ci-to-gha](index.md) migration — `portover run gitlab-ci-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .gitlab-ci.yml (GitLab CI)

```yaml
retry:
  max: 2
  when: runner_system_failure
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
# no built-in job retry; per-step:
- uses: nick-fields/retry@v3
  with:
    max_attempts: 3
    command: pytest -q
```

## What to watch for

GHA has no job-level automatic retry — the built-in options are re-running a failed job by hand from the UI, or wrapping the flaky command in a retry action. GitLab's `when:` filter (retry only on runner_system_failure, script_failure, job_execution_timeout...) has no counterpart either: a retry action retries on any non-zero exit. Retrying only infrastructure failures is not expressible, so treat this as a behaviour change, not a translation.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/retry.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
