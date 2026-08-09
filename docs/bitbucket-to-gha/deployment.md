# Migrate Bitbucket Pipelines deployment and manual triggers to GitHub Actions

**Directive:** `deployment: production / trigger: manual`

Part of the [bitbucket-to-gha](index.md) migration — `portover run bitbucket-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — bitbucket-pipelines.yml (Bitbucket Pipelines)

```yaml
- step:
    name: Deploy
    deployment: production
    trigger: manual
    script: [./deploy.sh]
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
deploy:
  environment: production     # deployment tracking + approvals + scoped secrets
  steps:
    - run: ./deploy.sh
```

## What to watch for

`deployment:` and GHA environments line up well — both track deployments per environment and both scope secrets to them. That also solves `trigger: manual`: Bitbucket pauses the step until someone clicks, and the GHA equivalent is an environment with required reviewers, which pauses the job the same way. So a manual deployment step needs no extra plumbing beyond configuring reviewers on the environment in repository settings. A `trigger: manual` step WITHOUT a deployment gets an environment invented for it, which portover flags — the alternative is a separate workflow_dispatch workflow.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/deployment.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
