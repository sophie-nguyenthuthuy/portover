# Migrate Buildkite variables and the buildkite-agent CLI to GitHub Actions

**Directive:** `$BUILDKITE_COMMIT, $BUILDKITE_BRANCH, buildkite-agent ...`

Part of the [buildkite-to-gha](index.md) migration — `portover run buildkite-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — Buildkite pipeline.yml

```yaml
commands:
  - docker build -t app:$BUILDKITE_COMMIT .
  - buildkite-agent artifact upload "dist/**"
  - buildkite-agent annotate "deployed" --style success
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
env:   # added automatically, so the scripts keep working
  BUILDKITE_COMMIT: ${{ github.sha }}

# buildkite-agent has no counterpart binary:
- uses: actions/upload-artifact@v4      # artifact upload
  with: {name: build, path: dist/**}
- run: echo "deployed" >> "$GITHUB_STEP_SUMMARY"   # annotate
```

## What to watch for

Variables are plain shell variables, so portover defines the ones your commands actually use as workflow-level `env:` from the github context and leaves the commands untouched. The `buildkite-agent` CLI is the sharper edge: it is installed on every Buildkite agent and does not exist on a GHA runner, so any command using it fails at runtime rather than at conversion. The mappings are `artifact upload` -> actions/upload-artifact, `artifact download` -> actions/download-artifact, `annotate` -> writing to $GITHUB_STEP_SUMMARY, `meta-data set/get` -> job outputs (`>> "$GITHUB_OUTPUT"` and `needs.<job>.outputs.<name>`), and `pipeline upload` (dynamic pipelines) -> a matrix built with fromJSON, since GHA cannot add jobs mid-run.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/variables.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
