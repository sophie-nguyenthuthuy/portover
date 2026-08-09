# Migrate GitLab CI only and except to GitHub Actions

**Directive:** `only: / except:`

Part of the [gitlab-ci-to-gha](index.md) migration — `portover run gitlab-ci-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .gitlab-ci.yml (GitLab CI)

```yaml
only:
  - main
  - /^release-.*$/
except:
  - schedules
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
if: >-
  (github.ref_name == 'main' || startsWith(github.ref_name, 'release-'))
  && !(github.event_name == 'schedule')
```

## What to watch for

`only`/`except` are the superseded form of `rules:` — GitLab still accepts them but you cannot mix the two in one job. Bare names are matched against refs, `/regex/` entries become startsWith/contains, and the keywords (branches, tags, merge_requests, schedules, api, web) map to GHA event names. Refs and keywords in one list are ORed, matching GitLab.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/only_except.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
