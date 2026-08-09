# Migrate Drone document kinds to GitHub Actions

**Directive:** `kind: pipeline / secret / signature — and type: docker / exec / ssh`

Part of the [drone-to-gha](index.md) migration — `portover run drone-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .drone.yml (Drone CI)

```yaml
kind: pipeline
type: docker
name: default
---
kind: secret
name: docker_password
get:
  path: secret/data/docker
  name: password
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
# only pipelines produce jobs; the rest have no YAML equivalent:
#   kind: secret    -> a repository or organisation secret
#   kind: signature -> nothing (Drone's config signing)
```

## What to watch for

A .drone.yml is a stream of documents and only `kind: pipeline` ones become jobs. `kind: secret` declares where Drone fetches a secret (often Vault) — recreate it as a GitHub secret, or wire the same vault with hashicorp/vault-action. `kind: signature` is the HMAC that signs the config for unverified repositories and has no counterpart. The pipeline `type:` matters too: `docker` is the normal case, `exec` runs directly on an agent (closest to a self-hosted runner, and its steps have no images), and `ssh`/`kubernetes`/`digitalocean` types describe infrastructure GHA does not model, so those are flagged.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/kind.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
