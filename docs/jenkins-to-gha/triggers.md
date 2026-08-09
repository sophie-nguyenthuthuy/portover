# Migrate Jenkins triggers to GitHub Actions on:

**Directive:** `triggers { cron / pollSCM / upstream }`

Part of the [jenkins-to-gha](index.md) migration — `portover run jenkins-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — Jenkinsfile (declarative pipeline)

```groovy
triggers {
  cron('H 4 * * 1-5')
  pollSCM('H/5 * * * *')
}
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
on:
  schedule:
    - cron: "0 4 * * 1-5"
  push: {}
```

## What to watch for

Jenkins 'H' spreads load by hashing the job name; GHA needs a concrete value — portover substitutes 0 and flags it. pollSCM is obsolete: GHA is event-driven, `on: push` replaces polling. upstream(...) maps to `on: workflow_run` and needs the upstream workflow's name.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/triggers.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
