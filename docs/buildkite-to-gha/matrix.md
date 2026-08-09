# Migrate Buildkite matrix and parallelism to GitHub Actions

**Directive:** `matrix: (list or setup/adjustments) / parallelism: N`

Part of the [buildkite-to-gha](index.md) migration — `portover run buildkite-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — Buildkite pipeline.yml

```yaml
matrix:
  setup:
    os: [linux, macos]
    version: ["3.11", "3.12"]
command: pytest --os {{matrix.os}} -V {{matrix.version}}

# or a plain count:
parallelism: 4
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
strategy:
  matrix:
    os: [linux, macos]
    version: ["3.11", "3.12"]
steps:
  - run: pytest --os ${{ matrix.os }} -V ${{ matrix.version }}

# a plain count becomes an index matrix:
strategy:
  matrix:
    BUILDKITE_PARALLEL_JOB: [0, 1, 2, 3]
```

## What to watch for

Both build a cartesian product, and portover rewrites the interpolation as it goes: `{{matrix}}` (the single-dimension form) becomes `${{ matrix.value }}` and `{{matrix.os}}` becomes `${{ matrix.os }}`. `adjustments:` have no direct equivalent — a `skip:` adjustment maps onto matrix `exclude:`, while one that only tweaks a combination's settings maps onto `include:`, so those are reported rather than guessed. `parallelism: N` splits one step across N agents and works only because Buildkite sets BUILDKITE_PARALLEL_JOB/BUILDKITE_PARALLEL_JOB_COUNT for your test runner to shard on — portover recreates both from the matrix so the command keeps working (note the index is 0-based, as in Buildkite).

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/matrix.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
