# Migrate Buildkite command steps to GitHub Actions run steps

**Directive:** `command: / commands:`

Part of the [buildkite-to-gha](index.md) migration — `portover run buildkite-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — Buildkite pipeline.yml

```yaml
commands:
  - npm ci
  - npm test
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
steps:
  - uses: actions/checkout@v4
  - run: npm ci
  - run: npm test
```

## What to watch for

`command` and `commands` are the same key with two spellings; a string runs as one command and a list runs one per line. portover emits one `run:` step each so a failure points at a single command. Two Buildkite habits need attention afterwards: agents often have tooling preinstalled that a GitHub-hosted runner does not, so add the matching setup-* action; and `buildkite-agent` calls inside a command (artifact upload/download, annotate, meta-data) have no equivalent binary on a GHA runner — those are flagged separately.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/command.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
