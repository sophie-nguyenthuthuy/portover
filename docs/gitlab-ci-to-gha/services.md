# Migrate GitLab CI services to GitHub Actions service containers

**Directive:** `services: [postgres:16, {name, alias}]`

Part of the [gitlab-ci-to-gha](index.md) migration — `portover run gitlab-ci-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .gitlab-ci.yml (GitLab CI)

```yaml
services:
  - postgres:16
  - name: redis:7
    alias: cache
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
services:
  postgres:
    image: postgres:16
    env: { POSTGRES_PASSWORD: postgres }
  cache:
    image: redis:7
```

## What to watch for

Both systems run sidecars on a shared network, but the hostname rule differs and this is where migrations break: in GitLab a service is reachable at its image name or `alias`, in GHA at its *key* in the services map. portover uses the alias when there is one and the image's base name otherwise. Also note GHA does not read GitLab's `POSTGRES_PASSWORD`-style variables from the job automatically — the service needs its own `env:`, and portover seeds the well-known ones.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/services.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
