# Migrate Woodpecker plugins to GitHub Actions

**Directive:** `settings: (a plugin step)`

Part of the [woodpecker-to-gha](index.md) migration — `portover run woodpecker-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .woodpecker.yml (Woodpecker CI)

```yaml
- name: publish
  image: woodpeckerci/plugin-docker-buildx
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

A step with `settings:` and no `commands:` is a plugin — a container configured through PLUGIN_* environment variables, which is what an action does with `with:`. Woodpecker's own plugins live under the woodpeckerci/ namespace but many configs still use Drone's plugins/ images, so both are recognised. Unrecognised plugins become a visible TODO step that keeps their settings as PLUGIN_* env, so nothing is lost silently, and `from_secret` values are rewritten to `${{ secrets.* }}` on the way through.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/settings.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
