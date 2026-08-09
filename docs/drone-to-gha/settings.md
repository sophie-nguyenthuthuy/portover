# Migrate Drone plugins to GitHub Actions

**Directive:** `settings: (a plugin step)`

Part of the [drone-to-gha](index.md) migration — `portover run drone-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .drone.yml (Drone CI)

```yaml
- name: publish
  image: plugins/docker
  settings:
    repo: acme/app
    tags: latest
    username: {from_secret: docker_user}
    password: {from_secret: docker_pass}
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
- uses: docker/login-action@v3
  with:
    username: ${{ secrets.DOCKER_USER }}
    password: ${{ secrets.DOCKER_PASS }}
- uses: docker/build-push-action@v6
  with:
    push: true
    tags: acme/app:latest
```

## What to watch for

A Drone step with `settings:` and no `commands:` is a plugin — a container whose behaviour is driven by PLUGIN_* environment variables. Actions are the direct counterpart and the common plugins translate: plugins/docker becomes docker/build-push-action (plus login), plugins/github-release becomes softprops/action-gh-release, plugins/s3 becomes the AWS CLI after configure-aws-credentials. Anything unrecognised becomes a visible TODO step carrying its settings, so nothing is silently dropped — and `from_secret` values are rewritten to `${{ secrets.* }}` on the way through.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/settings.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
