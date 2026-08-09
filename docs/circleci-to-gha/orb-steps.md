# Migrate CircleCI orb command steps

**Directive:** `- <orb-alias>/<command>`

Part of the [circleci-to-gha](index.md) migration — `portover run circleci-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .circleci/config.yml (CircleCI)

```yaml
- node/install-packages
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
- uses: actions/setup-node@v4
- run: npm ci
```

## What to watch for

Orb commands are arbitrary packaged logic. Portover identifies the source orb but leaves the exact action and inputs for review.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/orb_steps.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
