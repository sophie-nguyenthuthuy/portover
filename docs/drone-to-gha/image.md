# Migrate the Drone step image to GitHub Actions

**Directive:** `image: / pull:`

Part of the [drone-to-gha](index.md) migration — `portover run drone-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .drone.yml (Drone CI)

```yaml
- name: build
  image: golang:1.22
  pull: always
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
jobs:
  default:
    container: golang:1.22    # if every step shares it
    steps:
      - name: build
        run: go build
```

## What to watch for

Where the image ends up is decided by the steps mapping (job `container:` when shared, `docker run` when not), so this mapping only records it. `pull: always|if-not-exists|never` has no GHA counterpart — GHA pulls when the image is absent and there is no policy knob — so it is dropped. An image from a private registry needs `container.credentials` or a docker/login-action step, which is flagged since the credentials cannot be inferred.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/image.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
