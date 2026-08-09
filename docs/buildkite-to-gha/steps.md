# Migrate Buildkite steps to GitHub Actions jobs

**Directive:** `steps: [command / wait / block / input / trigger / group]`

Part of the [buildkite-to-gha](index.md) migration — `portover run buildkite-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — Buildkite pipeline.yml

```yaml
steps:
  - label: Build
    key: build
    command: make build
  - wait
  - label: Test
    command: make test
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
jobs:
  build:
    name: Build
    steps:
      - uses: actions/checkout@v4
      - run: make build
  test:
    needs: build      # the wait barrier
    name: Test
    steps:
      - uses: actions/checkout@v4
      - run: make test
```

## What to watch for

Buildkite and GHA already agree that work runs concurrently by default, so most steps become jobs with no `needs:` at all. The ordering comes from `wait` barriers and `depends_on`, which the wait and depends_on pages cover. A Buildkite step is a whole job, not a GHA step: it gets its own agent and its own checkout, so its `command:` list becomes that job's `run:` steps. Step `key:`s become the GHA job ids (that is what `depends_on` references); a step with only a label gets a slugged id, and emoji-prefixed labels like ':docker: Build' keep the readable text as the job `name:`.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/steps.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
