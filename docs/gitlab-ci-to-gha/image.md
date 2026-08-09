# Migrate GitLab CI image to GitHub Actions container

**Directive:** `image: name / image: {name, entrypoint}`

Part of the [gitlab-ci-to-gha](index.md) migration — `portover run gitlab-ci-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .gitlab-ci.yml (GitLab CI)

```yaml
image: python:3.12
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
runs-on: ubuntu-latest
container: python:3.12
```

## What to watch for

GitLab runs every job in a container by default; GHA runs on the runner VM unless you ask for one, so `image:` becomes `container:` on top of `runs-on:`. Often the better migration is to drop the container entirely and use a setup action (`actions/setup-python@v5`) — that is faster and gives you dependency caching. Keep the container when the image carries tools you actually need. `entrypoint: [""]` is a GitLab workaround for images with an entrypoint and has no GHA counterpart: container steps override the entrypoint already.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/image.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
