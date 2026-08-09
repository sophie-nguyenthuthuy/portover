# Migrate GitLab CI runner tags to GitHub Actions runs-on

**Directive:** `tags: [docker, linux]`

Part of the [gitlab-ci-to-gha](index.md) migration — `portover run gitlab-ci-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .gitlab-ci.yml (GitLab CI)

```yaml
tags:
  - docker
  - linux
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
runs-on: [self-hosted, docker, linux]
```

## What to watch for

Both systems pick a runner by label, so tags become `runs-on` labels. The catch is that a GitLab tag usually names a runner YOU registered, which means the honest translation is a self-hosted runner with the same labels — portover adds `self-hosted` for that reason. If the tag was only picking a size or an OS on GitLab's shared fleet (saas-linux-medium-amd64 and friends), replace it with the matching GitHub-hosted label (ubuntu-latest, or a larger runner your org has configured) instead.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/tags.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
