# Migrate Woodpecker matrix to GitHub Actions

**Directive:** `matrix: {VAR: [...], include: [...]}`

Part of the [woodpecker-to-gha](index.md) migration — `portover run woodpecker-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .woodpecker.yml (Woodpecker CI)

```yaml
matrix:
  GO_VERSION:
    - "1.21"
    - "1.22"
  DATABASE:
    - postgres
    - mysql

steps:
  - name: test
    image: golang:${GO_VERSION}
    commands:
      - go test -tags $DATABASE ./...
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
strategy:
  matrix:
    GO_VERSION: ["1.21", "1.22"]
    DATABASE: [postgres, mysql]
env:
  GO_VERSION: ${{ matrix.GO_VERSION }}   # so $GO_VERSION still works
  DATABASE: ${{ matrix.DATABASE }}
container: golang:${{ matrix.GO_VERSION }}
```

## What to watch for

Both build a cartesian product from named variables, so the axes carry over directly, and `include:` rows map onto matrix `include:`. The part worth understanding is how the values are read: Woodpecker exposes each matrix variable as an ENVIRONMENT variable inside the step, which is why commands say `$GO_VERSION`. portover keeps that working by defining the job's `env:` from the matrix, so no command needs editing. The exception is `image:`, which GHA evaluates itself rather than through a shell — there the `${VAR}` is rewritten to `${{ matrix.VAR }}`.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/matrix.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
