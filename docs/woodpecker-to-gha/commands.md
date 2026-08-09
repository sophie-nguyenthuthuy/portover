# Migrate Woodpecker commands to GitHub Actions run steps

**Directive:** `commands: [...]`

Part of the [woodpecker-to-gha](index.md) migration — `portover run woodpecker-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .woodpecker.yml (Woodpecker CI)

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
```

## What to watch for

Woodpecker runs a step's commands in one shell with `set -e`, so the list becomes a single `run:` block rather than one step per line — that keeps `cd` and exported variables working across lines, which splitting would silently break. When the workflow's steps use different images the block instead runs `docker run` against that step's image, bind-mounting the workspace so files from earlier steps are still present, and forwarding the step's environment with -e.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/commands.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
