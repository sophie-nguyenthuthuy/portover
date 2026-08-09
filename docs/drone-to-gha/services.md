# Migrate Drone services to GitHub Actions service containers

**Directive:** `services: [{name, image, environment}]`

Part of the [drone-to-gha](index.md) migration — `portover run drone-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .drone.yml (Drone CI)

```yaml
services:
  - name: database
    image: postgres:16
    environment:
      POSTGRES_PASSWORD: secret
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
services:
  database:
    image: postgres:16
    env:
      POSTGRES_PASSWORD: secret
```

## What to watch for

Close to a rename — both run sidecars on a shared network for the duration, and in both the service is reachable at its NAME as hostname, so connection strings usually need no change. Drone's `environment:` becomes `env:`, including `from_secret` references, which are rewritten to `${{ secrets.* }}`. Where they differ: GHA waits only for the container to start unless you give it `options: --health-cmd`, so a service that needs a moment to become ready (Postgres, MySQL) should get a healthcheck — portover adds one for the databases it recognises.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/services.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
