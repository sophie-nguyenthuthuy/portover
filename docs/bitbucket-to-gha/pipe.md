# Migrate Bitbucket Pipes to GitHub Actions

**Directive:** `- pipe: atlassian/aws-s3-deploy:1.1.0`

Part of the [bitbucket-to-gha](index.md) migration — `portover run bitbucket-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — bitbucket-pipelines.yml (Bitbucket Pipelines)

```yaml
- pipe: atlassian/slack-notify:2.0.0
  variables:
    WEBHOOK_URL: $SLACK_WEBHOOK
    MESSAGE: "Build finished"
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
- uses: slackapi/slack-github-action@v2
  with:
    webhook: ${{ secrets.SLACK_WEBHOOK }}
    # MESSAGE -> payload
```

## What to watch for

A pipe is a Docker image with inputs — the same idea as an action, so the common Atlassian pipes have direct counterparts and portover translates those. Two things always need your attention: pipe `variables:` are passed as environment variables while action inputs go under `with:`, so names rarely match one-to-one; and any pipe variable holding a credential was a Bitbucket repository variable, which must be recreated as a GitHub secret. A `docker://` pipe is just a container — run it with `docker run` in a `run:` step. Unrecognised pipes become a visible TODO step rather than disappearing.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/pipe.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
