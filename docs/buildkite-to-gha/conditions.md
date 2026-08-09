# Migrate Buildkite if, branches and skip to GitHub Actions

**Directive:** `if: / branches: / skip:`

Part of the [buildkite-to-gha](index.md) migration — `portover run buildkite-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — Buildkite pipeline.yml

```yaml
if: build.branch == "main" && build.tag == null
branches: "main release/*"
skip: "not ready"
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
if: github.ref_name == 'main' && github.ref_type != 'tag'
```

## What to watch for

Buildkite's `if:` language is already infix, so it reads close to a GHA expression once the operands are swapped: build.branch -> github.ref_name, build.commit -> github.sha, build.pull_request.id != null -> github.event_name == 'pull_request'. `build.tag == null` is the one that changes shape — in GHA that is a statement about the ref TYPE (github.ref_type != 'tag'). The older `branches:` filter is a space-separated glob list where a leading `!` excludes, which becomes an OR of ref comparisons. `skip:` takes a string reason in Buildkite and shows it in the UI; GHA has no skipped-with-reason state, so it becomes `if: false` with the reason kept as a comment-worthy flag.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/conditions.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
