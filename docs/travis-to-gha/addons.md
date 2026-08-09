# Migrate Travis addons to GitHub Actions

**Directive:** `addons: apt / chrome / firefox / ...`

Part of the [travis-to-gha](index.md) migration — `portover run travis-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .travis.yml (Travis CI)

```yaml
addons:
  apt:
    packages:
      - libpq-dev
      - graphviz
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
- run: sudo apt-get update && sudo apt-get install -y libpq-dev graphviz
```

## What to watch for

apt packages become one explicit install step. chrome/firefox are preinstalled on GHA Ubuntu runners and are dropped. Other addons (sonarcloud, sauce_connect, ...) map to their own marketplace actions — flagged with the addon name so you can search for it.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/addons.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
