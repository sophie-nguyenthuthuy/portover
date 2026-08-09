# Migrate CircleCI orbs to GitHub Actions

**Directive:** `orbs: name: namespace/orb@x.y`

Part of the [circleci-to-gha](index.md) migration — `portover run circleci-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .circleci/config.yml (CircleCI)

```yaml
orbs:
  node: circleci/node@5.2.0
  aws-cli: circleci/aws-cli@4.1.3
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
# orbs have no declaration block — each orb command becomes an action
# at the step that used it:
steps:
  - uses: actions/setup-node@v4      # was: node/install-packages
  - uses: aws-actions/configure-aws-credentials@v4   # was: aws-cli/setup
```

## What to watch for

Orbs are packaged step bundles; GHA's equivalent unit is the action, declared inline at the step. portover records the orb aliases here so each `orb/command` step can be flagged with its orb name — see the orb-steps page. Common swaps: circleci/node -> actions/setup-node, circleci/python -> actions/setup-python, circleci/aws-cli -> aws-actions/configure-aws-credentials (prefer OIDC over stored keys), circleci/slack -> slackapi/slack-github-action, circleci/docker -> docker/build-push-action.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/orbs.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
