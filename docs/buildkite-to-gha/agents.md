# Migrate Buildkite agents to GitHub Actions runs-on

**Directive:** `agents: {queue: default, os: linux}`

Part of the [buildkite-to-gha](index.md) migration — `portover run buildkite-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — Buildkite pipeline.yml

```yaml
agents:
  queue: builders
  os: linux
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
runs-on: [self-hosted, builders, linux]
```

## What to watch for

Buildkite is agent-based: you run the machines, and `agents:` is a tag query that picks one. The faithful translation is a self-hosted runner carrying the same labels, which is what portover emits — but it is worth asking whether the step needs a specific machine at all, because GitHub-hosted runners (`runs-on: ubuntu-latest`) remove the fleet you were maintaining. A queue named for an OS or size usually translates to a hosted runner instead; a queue named for private network access or special hardware genuinely needs self-hosted.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/agents.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
