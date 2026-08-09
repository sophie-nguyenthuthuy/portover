# Migrate Woodpecker services to GitHub Actions service containers

**Directive:** `services: (map or list)`

Part of the [woodpecker-to-gha](index.md) migration — `portover run woodpecker-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .woodpecker.yml (Woodpecker CI)

```yaml
services:
  database:                 # map form
    image: postgres:16
    environment:
      - POSTGRES_PASSWORD=secret

services:                   # list form, 2.x onwards
  - name: database
    image: postgres:16
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
services:
  database:
    image: postgres:16
    env:
      POSTGRES_PASSWORD: secret
    options: --health-cmd pg_isready --health-interval 10s --health-retries 5
```

## What to watch for

Both spellings are accepted and normalise to the same thing. The hostname rule matches too — the service is reachable at its name — so connection strings usually need no change. What GHA adds is readiness: it waits only for the container to start, so a database that takes a moment to accept connections needs a healthcheck, and portover attaches one for the images it recognises. Woodpecker's `environment:` list form becomes the container's `env:` map.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/services.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
