# Migrate Drone environment and from_secret to GitHub Actions

**Directive:** `environment: {NAME: value, NAME: {from_secret: x}}`

Part of the [drone-to-gha](index.md) migration — `portover run drone-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .drone.yml (Drone CI)

```yaml
environment:
  GOOS: linux
  DOCKER_PASSWORD:
    from_secret: docker_password
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
env:
  GOOS: linux
  DOCKER_PASSWORD: ${{ secrets.DOCKER_PASSWORD }}
```

## What to watch for

Plain values map straight to the step's `env:`. `from_secret:` is the interesting one — it names a secret stored in Drone (repository, organisation, or a `kind: secret` document), never a value in the file, so nothing sensitive is carried over. portover rewrites the reference to `${{ secrets.NAME }}`, upper-casing the Drone name because GitHub secret names are case-insensitive and conventionally upper-case; create each one under Settings > Secrets and variables.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/environment.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
