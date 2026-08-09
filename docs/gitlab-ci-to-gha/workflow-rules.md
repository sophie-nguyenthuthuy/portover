# Migrate GitLab CI workflow rules to GitHub Actions triggers

**Directive:** `workflow: rules / name`

Part of the [gitlab-ci-to-gha](index.md) migration — `portover run gitlab-ci-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .gitlab-ci.yml (GitLab CI)

```yaml
workflow:
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == "main"
    - if: $CI_COMMIT_TAG
    - when: never
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
on:
  pull_request:
  push:
    branches: [main]
    tags: ["*"]
```

## What to watch for

This is the one place where GitLab rules become GHA *triggers* rather than `if:` conditions, because they decide whether the run happens at all. portover reads the rule list for the pipeline sources and branch/tag conditions it can recognise and builds `on:` from them; a trailing `when: never` is the GitLab idiom for 'nothing else runs' and needs no translation, since GHA only triggers on what you list. Anything more involved is flagged — an over-broad trigger is a wasted run, but a wrong one silently stops building.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/workflow_rules.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
