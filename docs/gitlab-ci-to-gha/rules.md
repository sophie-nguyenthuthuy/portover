# Migrate GitLab CI rules to GitHub Actions if conditions

**Directive:** `rules: [{if, changes, exists, when, allow_failure}]`

Part of the [gitlab-ci-to-gha](index.md) migration — `portover run gitlab-ci-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .gitlab-ci.yml (GitLab CI)

```yaml
rules:
  - if: $CI_COMMIT_BRANCH == "main"
  - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    when: manual
  - when: never
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
if: >-
  github.ref_name == 'main' ||
  github.event_name == 'pull_request'
```

## What to watch for

The semantics differ in a way that matters: GitLab evaluates rules top-down and stops at the FIRST match, so a later rule never overrides an earlier one. GHA has a single `if:` per job. portover ORs together the conditions that include the job and negates any `when: never` rule that precedes them, which reproduces first-match for the shapes people actually write. A trailing bare `when: never` is just 'nothing else runs' and needs no output. Per-rule `when: manual` cannot be folded into a boolean at all — that job wants a workflow_dispatch trigger or an environment with required reviewers, so it is flagged. Variables are translated to github contexts: $CI_COMMIT_BRANCH -> github.ref_name, $CI_PIPELINE_SOURCE == "merge_request_event" -> github.event_name == 'pull_request'.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/rules.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
