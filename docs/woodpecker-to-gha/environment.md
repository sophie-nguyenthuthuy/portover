# Migrate Woodpecker environment and secrets to GitHub Actions

**Directive:** `environment: (map or KEY=value list) / secrets: / from_secret`

Part of the [woodpecker-to-gha](index.md) migration — `portover run woodpecker-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .woodpecker.yml (Woodpecker CI)

```yaml
environment:
  - GOOS=linux              # list form
  TOKEN:
    from_secret: api_token  # map form
secrets: [docker_password]  # pre-2.0 spelling
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
env:
  GOOS: linux
  TOKEN: ${{ secrets.API_TOKEN }}
  DOCKER_PASSWORD: ${{ secrets.DOCKER_PASSWORD }}
```

## What to watch for

`environment:` accepts a map or a list of `KEY=value` strings, and portover normalises both. Secrets have two spellings across Woodpecker versions: the modern `from_secret:` on a variable, and the older top-level `secrets: [name]` list, which injected each secret as an upper-cased environment variable of the same name — both become `${{ secrets.NAME }}`. Nothing sensitive is carried over either way, because the values live in Woodpecker's settings, not in this file; recreate them under Settings > Secrets and variables.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/environment.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
