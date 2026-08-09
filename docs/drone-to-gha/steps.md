# Migrate Drone steps to GitHub Actions

**Directive:** `steps: [{name, image, commands}]`

Part of the [drone-to-gha](index.md) migration — `portover run drone-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .drone.yml (Drone CI)

```yaml
steps:
  - name: build
    image: golang:1.22
    commands:
      - go build
  - name: test
    image: golang:1.22
    commands:
      - go test ./...
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
jobs:
  default:
    container: golang:1.22      # every step shares one image
    steps:
      - uses: actions/checkout@v4
      - name: build
        run: go build
      - name: test
        run: go test ./...
```

## What to watch for

Drone steps share the workspace volume, so files written by one step are simply there for the next — that is GHA's STEP behaviour, not its job behaviour, which is why a Drone pipeline becomes one job rather than one job per step. The catch is images: Drone names one per step, GHA has one per job. When every step uses the same image portover sets the job's `container:` and emits plain `run:` steps. When they differ it cannot use `container:` at all (a `docker run` inside a job container has no daemon), so each step runs `docker run` against its own image with the workspace bind-mounted — faithful, and the shared files still work. If an image was only supplying a toolchain, the cleaner migration is a setup-* action plus a plain `run:`.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/steps.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
