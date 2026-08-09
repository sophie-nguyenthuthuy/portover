# Migrate the remaining Woodpecker step settings to GitHub Actions

**Directive:** `image / failure / detach / directory / group / privileged / pull`

Part of the [woodpecker-to-gha](index.md) migration — `portover run woodpecker-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .woodpecker.yml (Woodpecker CI)

```yaml
- name: lint
  image: golangci/golangci-lint
  failure: ignore
  directory: backend
  commands: [golangci-lint run]
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
- name: lint
  continue-on-error: true
  working-directory: backend
  run: golangci-lint run
```

## What to watch for

`failure: ignore` is `continue-on-error: true` and `directory:` is `working-directory:`. `detach: true` starts a long-running step alongside the others — GHA service containers are the equivalent, so moving it to `services:` is usually right and portover flags it rather than guessing. `group:` (concurrent steps) cannot be expressed with GHA steps at all, since those are strictly sequential. `privileged`, `pull` and `backend_options` describe the Woodpecker agent's sandbox and have no counterpart: a GHA job gets its own VM, and there is no image pull policy.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/step_settings.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
