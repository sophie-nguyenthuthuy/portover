# Migrate Jenkins tools blocks to GitHub Actions setup-* actions

**Directive:** `tools { jdk / nodejs / maven / go }`

Part of the [jenkins-to-gha](index.md) migration — `portover run jenkins-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — Jenkinsfile (declarative pipeline)

```groovy
tools {
  jdk 'jdk17'
  nodejs 'node20'
}
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
steps:
  - uses: actions/setup-java@v4
    with: { distribution: temurin, java-version: "17" }
  - uses: actions/setup-node@v4
    with: { node-version: "20" }
```

## What to watch for

Jenkins tool names are labels configured on the controller; portover extracts the version number from the label — check it. maven: ubuntu-latest runners ship mvn; setup-java handles the JDK.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/tools.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
