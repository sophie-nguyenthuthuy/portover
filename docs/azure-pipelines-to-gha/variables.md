# Migrate Azure Pipelines variables to GitHub Actions env

**Directive:** `variables: (mapping, list, group or template)`

Part of the [azure-pipelines-to-gha](index.md) migration — `portover run azure-pipelines-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — azure-pipelines.yml (Azure Pipelines)

```yaml
variables:
  appEnv: production
  - group: prod-secrets
  - name: buildConfig
    value: Release
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
env:
  appEnv: production
  buildConfig: Release
  # variable group 'prod-secrets' -> repository secrets or an Environment
```

## What to watch for

All three spellings — a plain mapping, a list of name/value pairs, and the `${{ }}` template form — become `env:`. The one that cannot be translated is `- group:`: a variable group lives in Azure Library, not in the YAML, so portover cannot see its contents. Recreate those as repository or Environment secrets. Secret variables are the same story: they are never in the file, so nothing is silently carried over in plaintext.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/variables.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
