# Migrate Bitbucket Pipelines image to GitHub Actions container

**Directive:** `image: name / image: {name, username, password}`

Part of the [bitbucket-to-gha](index.md) migration — `portover run bitbucket-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — bitbucket-pipelines.yml (Bitbucket Pipelines)

```yaml
image:
  name: private.registry/build:1.2
  username: $REGISTRY_USER
  password: $REGISTRY_PASS
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
container:
  image: private.registry/build:1.2
  credentials:
    username: ${{ secrets.REGISTRY_USER }}
    password: ${{ secrets.REGISTRY_PASS }}
```

## What to watch for

Every Bitbucket step runs in a container, so `image:` is mandatory there and optional in GHA — which means the better migration is often to drop the container and use `runs-on: ubuntu-latest` with a setup action, since that gets you caching and preinstalled tooling. Keep the container when the image carries tools you need. Registry credentials map onto `container.credentials`, and the `$VAR` references become GitHub secrets. `run-as-user` maps to `container.options: --user N`.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/image.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
