# Migrate CircleCI remote Docker setup

**Directive:** `- setup_remote_docker`

Part of the [circleci-to-gha](index.md) migration — `portover run circleci-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .circleci/config.yml (CircleCI)

```yaml
- setup_remote_docker
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
# remove it; Docker is already available on ubuntu runners
```

## What to watch for

If the job itself runs in a container, Docker access differs; use a host runner or a purpose-built build action.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/setup_remote_docker.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
