# Migrate GitLab CI trigger to GitHub Actions

**Directive:** `trigger: project / include / strategy`

Part of the [gitlab-ci-to-gha](index.md) migration — `portover run gitlab-ci-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .gitlab-ci.yml (GitLab CI)

```yaml
deploy-downstream:
  trigger:
    project: my-group/deployer
    branch: main
    strategy: depend
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
deploy-downstream:
  uses: my-org/deployer/.github/workflows/deploy.yml@main
  secrets: inherit
```

## What to watch for

A multi-project trigger becomes a reusable workflow call — note the job then uses `uses:` INSTEAD of `runs-on`/`steps`, and the called workflow must declare `on: workflow_call`. `strategy: depend` (wait for the downstream result) is the default for a called workflow, so that comes for free. A child-pipeline trigger (`trigger: include:`) has no real equivalent: put those jobs in the same workflow, or split them into a reusable workflow too. If you need to fire and forget across repos, that is `repository_dispatch` plus a token.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/trigger.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
