# azure-pipelines-to-gha: azure-pipelines.yml (Azure Pipelines) → .github/workflows/*.yml (GitHub Actions)

Run it: `portover run azure-pipelines-to-gha <dir>` (dry run) then `--write`.

One page per directive:

- [`- script / bash / pwsh / powershell / checkout`](steps.md) — Migrate Azure Pipelines script steps to GitHub Actions
- [`trigger: branches / tags / paths / none`](trigger.md) — Migrate Azure Pipelines trigger to GitHub Actions on push
- [`pr: branches / paths / drafts / none`](pr.md) — Migrate Azure Pipelines pr triggers to GitHub Actions
- [`- task: Name@version`](task.md) — Migrate Azure Pipelines tasks to GitHub Actions
- [`- publish: path / - download: current`](publish-download.md) — Migrate Azure Pipelines publish and download shortcuts to GitHub Actions
- [`schedules: [{cron, branches, always}]`](schedules.md) — Migrate Azure Pipelines schedules to GitHub Actions
- [`pool: vmImage / name / demands`](pool.md) — Migrate Azure Pipelines pool to GitHub Actions runs-on
- [`- template: steps/build.yml@repo`](template.md) — Migrate Azure Pipelines templates to GitHub Actions
- [`parameters: [{name, type, default, values}]`](parameters.md) — Migrate Azure Pipelines parameters to workflow_dispatch inputs
- [`variables: (pipeline level)`](pipeline-variables.md) — Migrate Azure Pipelines pipeline-level variables to GitHub Actions
- [`strategy: matrix / parallel / maxParallel`](strategy.md) — Migrate Azure Pipelines strategy matrix to GitHub Actions
- [`condition: and(succeeded(), eq(...))`](condition.md) — Migrate Azure Pipelines conditions to GitHub Actions if
- [`variables: (mapping, list, group or template)`](variables.md) — Migrate Azure Pipelines variables to GitHub Actions env
- [`container / services / timeoutInMinutes / continueOnError / workspace`](job-settings.md) — Migrate Azure Pipelines job settings to GitHub Actions
- [`resources: repositories / containers / pipelines — plus extends and name`](resources.md) — Migrate Azure Pipelines resources, extends and name to GitHub Actions
- [`stages: [{stage, dependsOn, condition, jobs}]`](stages.md) — Migrate Azure Pipelines stages to GitHub Actions
- [`jobs: [{job, dependsOn, condition, steps}] / steps:`](jobs.md) — Migrate Azure Pipelines jobs to GitHub Actions jobs
- [`$(Build.SourceVersion), $(Build.SourceBranchName), $(Agent.OS), ...`](predefined-variables.md) — Migrate Azure Pipelines predefined variables to GitHub Actions
