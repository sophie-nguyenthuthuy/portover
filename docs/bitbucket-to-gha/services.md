# Migrate Bitbucket Pipelines services to GitHub Actions service containers

**Directive:** `services: [postgres, redis]`

Part of the [bitbucket-to-gha](index.md) migration — `portover run bitbucket-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — bitbucket-pipelines.yml (Bitbucket Pipelines)

```yaml
definitions:
  services:
    postgres:
      image: postgres:16
      variables:
        POSTGRES_PASSWORD: secret

# in a step:
services:
  - postgres
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
services:
  postgres:
    image: postgres:16
    env:
      POSTGRES_PASSWORD: secret
```

## What to watch for

Bitbucket splits the definition (under `definitions.services`) from the use (a step's `services:` list); GHA declares the container inline on the job, so portover resolves the reference. Note the hostname rule: Bitbucket services listen on localhost from the step's point of view, while a GHA service is reachable at its key in the services map — for a container job, `postgres:5432` rather than `localhost:5432`. Bitbucket's `variables:` become the container's `env:`, and `memory:` has no equivalent (GHA does not cap service memory).

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/services.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
