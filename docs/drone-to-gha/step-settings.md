# Migrate the remaining Drone step settings to GitHub Actions

**Directive:** `failure / detach / privileged / volumes / depends_on / resources`

Part of the [drone-to-gha](index.md) migration — `portover run drone-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .drone.yml (Drone CI)

```yaml
- name: lint
  image: golangci/golangci-lint
  failure: ignore
  commands: [golangci-lint run]

- name: proxy
  image: nginx
  detach: true
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
- name: lint
  continue-on-error: true
  run: golangci-lint run

# detach has no equivalent — start it in the background:
- run: docker run -d --name proxy nginx
```

## What to watch for

`failure: ignore` is `continue-on-error: true`. `detach: true` starts a long-running step alongside the others, which is what GHA service containers do — moving it to `services:` is usually the right answer, so it is flagged rather than translated blindly. `privileged`, `volumes` and `resources` all describe the Docker runner's sandbox and have no counterpart: GHA jobs get a whole VM, so privileged work generally just works, host volumes do not exist, and CPU/memory limits are fixed by the runner size.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/step_settings.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
