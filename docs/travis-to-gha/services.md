# Migrate Travis services to GitHub Actions service containers

**Directive:** `services: postgresql / redis / mysql / docker ...`

Part of the [travis-to-gha](index.md) migration — `portover run travis-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .travis.yml (Travis CI)

```yaml
services:
  - postgresql
  - redis
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
services:
  postgres:
    image: postgres:16
    env: { POSTGRES_PASSWORD: postgres }
    ports: ["5432:5432"]
    options: --health-cmd pg_isready --health-interval 10s --health-retries 5
  redis:
    image: redis:7
    ports: ["6379:6379"]
```

## What to watch for

Travis services listened on localhost with no auth; GHA service containers need explicit ports and (for postgres/mysql) a password — update your test config accordingly. `docker` needs no service at all: the docker daemon is already available on GHA runners.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/services.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
