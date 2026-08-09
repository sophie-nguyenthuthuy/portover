# Migrate Azure Pipelines tasks to GitHub Actions

**Directive:** `- task: Name@version`

Part of the [azure-pipelines-to-gha](index.md) migration — `portover run azure-pipelines-to-gha` applies this mapping (and every other one on this page's index) automatically.

## Before — azure-pipelines.yml (Azure Pipelines)

```yaml
- task: UsePythonVersion@0
  inputs:
    versionSpec: "3.12"
- task: PublishBuildArtifacts@1
  inputs:
    pathToPublish: dist
    artifactName: drop
```

## After — .github/workflows/*.yml (GitHub Actions)

```yaml
- uses: actions/setup-python@v5
  with:
    python-version: "3.12"
- uses: actions/upload-artifact@v4
  with:
    name: drop
    path: dist
```

## What to watch for

Tasks are Azure's equivalent of actions, and the common ones have direct counterparts — portover translates the setup, cache, artifact and shell tasks including their inputs. Tasks that only wrap a CLI (DotNetCoreCLI, NuGetCommand, CopyFiles, ArchiveFiles) become plain `run:` steps, which is usually clearer than hunting for an equivalent action. Azure-specific deployment tasks (AzureWebApp, AzureRmWebAppDeployment) map to the official azure/* actions but need azure/login and an OIDC or credentials secret first, so those are flagged rather than guessed. Anything unrecognised is flagged with the task name so you can search the marketplace.

---

*Wrong or incomplete? This page is generated from one small file — [`mappings/task.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*
