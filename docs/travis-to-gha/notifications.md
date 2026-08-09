# Migrate Travis notifications to GitHub Actions

**Directive:** `notifications: email / slack / ...`

Part of the [travis-to-gha](index.md) migration — `portover run travis-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .travis.yml (Travis CI)

```yaml
notifications:
  email: false
  slack: myteam:token
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
# GitHub already emails you on failed runs (Settings > Notifications).
# For Slack, add a final step:
- if: failure()
  uses: slackapi/slack-github-action@v2
```

## What to watch for

email: false is the happy case — GHA only notifies on failure by default, which is what most people were trying to configure. Slack tokens embedded in .travis.yml are a secret-hygiene bug anyway: rotate the token and move it to a repo secret with slackapi's action.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/notifications.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
