# Migrate GitLab CI include to GitHub Actions

**Directive:** `include: local / project / remote / template`

Part of the [gitlab-ci-to-gha](index.md) migration — `portover run gitlab-ci-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — .gitlab-ci.yml (GitLab CI)

```yaml
include:
  - local: /ci/tests.yml
  - template: Security/SAST.gitlab-ci.yml
  - project: my-group/ci-templates
    file: /deploy.yml
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
# no include chain — the closest equivalents are:
#   local   -> paste the jobs in, or make it a reusable workflow (workflow_call)
#   project -> a reusable workflow in another repo:
#              uses: my-org/ci-templates/.github/workflows/deploy.yml@main
#   template-> find the marketplace action (SAST -> github/codeql-action)
```

## What to watch for

portover only reads the file you point it at, so jobs defined in an include are NOT in the output — run portover against each included file too, or inline them first. GitLab's `template:` includes are GitLab-authored pipelines (SAST, Dependency Scanning, Code Quality); their GHA counterparts are marketplace actions or GitHub-native features like CodeQL and Dependabot, not a line-by-line translation.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/include.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
