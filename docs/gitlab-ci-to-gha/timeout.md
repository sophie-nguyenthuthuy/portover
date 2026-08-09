# Migrate GitLab CI timeout to GitHub Actions

**Directive:** `timeout: 1h 30m`

Part of the [gitlab-ci-to-gha](index.md) migration — `portover run gitlab-ci-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .gitlab-ci.yml (GitLab CI)

```yaml
timeout: 1h 30m
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
timeout-minutes: 90
```

## What to watch for

GitLab accepts human durations ('3 hours 30 minutes'); GHA takes whole minutes. Note the defaults differ sharply — GitLab defaults to 1 hour per job, GHA to 6 hours — so a job that relied on GitLab's default to kill a hang will now run six times longer. If a timeout mattered, set it explicitly.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/timeout.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
