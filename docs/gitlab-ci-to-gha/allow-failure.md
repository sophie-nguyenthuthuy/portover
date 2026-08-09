# Migrate GitLab CI allow_failure to GitHub Actions

**Directive:** `allow_failure: true / {exit_codes}`

Part of the [gitlab-ci-to-gha](index.md) migration — `portover run gitlab-ci-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .gitlab-ci.yml (GitLab CI)

```yaml
allow_failure: true
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
continue-on-error: true
```

## What to watch for

A direct translation. The visible difference is reporting: GitLab shows the job as 'passed with warnings' (orange), while GHA marks the run green and you have to open the job to see the failure. `allow_failure: {exit_codes: [137]}` — tolerate only specific exit codes — has no equivalent; handle it in the script with a trap or an explicit `|| exit 0` for the codes you accept.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/allow_failure.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
