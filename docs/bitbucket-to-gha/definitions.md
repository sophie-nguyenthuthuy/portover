# Migrate Bitbucket Pipelines definitions to GitHub Actions

**Directive:** `definitions: caches / services / steps`

Part of the [bitbucket-to-gha](index.md) migration — `portover run bitbucket-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — bitbucket-pipelines.yml (Bitbucket Pipelines)

```yaml
definitions:
  caches:
    sonar: ~/.sonar/cache
  services:
    postgres:
      image: postgres:16
      variables:
        POSTGRES_PASSWORD: secret
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
# no definitions block — each is inlined where it is used:
#   caches   -> actions/cache path in the job that listed it
#   services -> the job's services: map
```

## What to watch for

`definitions:` is a declaration area, not something that runs, so it produces no output of its own — portover records the entries and resolves them wherever a step references them. `definitions.steps` holds YAML-anchored step templates (`&build-step`), and anchors are the one construct portover's reader refuses rather than guesses at: if your config uses them, expand them first. The GHA equivalent of a shared step template is a composite action or a reusable workflow.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/definitions.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
