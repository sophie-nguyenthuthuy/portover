# Migrate CircleCI resource classes

**Directive:** `resource_class: medium`

Part of the [circleci-to-gha](index.md) migration — `portover run circleci-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .circleci/config.yml (CircleCI)

```yaml
resource_class: large
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
runs-on: ubuntu-latest  # select a larger runner in repository settings
```

## What to watch for

Runner sizes and billing tiers do not map one-to-one. Standard CircleCI classes stay on the generated runner; select a GHA larger-runner label or self-hosted label if the job needs more capacity.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/resource_class.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
