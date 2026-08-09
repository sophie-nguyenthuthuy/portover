# Migrate Drone commands to GitHub Actions run steps

**Directive:** `commands: [...]`

Part of the [drone-to-gha](index.md) migration — `portover run drone-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .drone.yml (Drone CI)

```yaml
- name: test
  image: golang:1.22
  commands:
    - go vet ./...
    - go test ./...
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
- name: test
  run: |
    go vet ./...
    go test ./...

# when the step's image differs from the rest of the pipeline:
- name: test
  run: |
    docker run --rm -i \
      -v "$PWD":/drone/src -w /drone/src golang:1.22 sh -e <<'DRONE_STEP'
    go vet ./...
    go test ./...
    DRONE_STEP
```

## What to watch for

Drone runs a step's commands with `set -e` in one shell, so the whole list becomes a single `run:` block rather than one step per line — that keeps `cd` and exported variables working across the lines, which splitting would break. The `docker run` form appears only when the pipeline's steps use different images; it bind-mounts the workspace so the files a previous step wrote are still there, and forwards the step's environment with -e.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/commands.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
