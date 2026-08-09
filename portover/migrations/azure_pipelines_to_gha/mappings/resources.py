"""resources / extends / name — the remaining pipeline-level keys."""

from portover.core import MappingMeta

SCOPE = "pipeline"

META = MappingMeta(
    id="resources",
    directive="resources: repositories / containers / pipelines — plus extends and name",
    title="Migrate Azure Pipelines resources, extends and name to GitHub Actions",
    before="""name: $(Date:yyyyMMdd)$(Rev:.r)

resources:
  repositories:
    - repository: templates
      type: git
      name: shared/ci-templates
  pipelines:
    - pipeline: upstream
      source: build-pipeline
      trigger: true

extends:
  template: templates/pipeline.yml@templates""",
    after="""run-name: build ${{ github.run_number }}

# repositories -> a second actions/checkout step with `repository:`
# pipelines (trigger) -> on: workflow_run
# extends -> a reusable workflow: uses: ./.github/workflows/pipeline.yml""",
    notes=(
        "These are the keys that describe a pipeline's relationship to things "
        "outside the file, so none of them translate mechanically. "
        "`resources.repositories` becomes an extra actions/checkout step (with "
        "a token for private repos); `resources.pipelines` with `trigger: true` "
        "is `on: workflow_run`; `resources.containers` become job "
        "`container:`/`services:` entries. `extends:` means the real pipeline "
        "lives in another file — that is a reusable workflow in GHA, and "
        "portover cannot see the template's contents, so it is always flagged. "
        "`name:` is Azure's build-number format, whose closest counterpart is "
        "`run-name:` (though the $(Date)/$(Rev) tokens have no equivalent)."
    ),
    manual=True,
    priority=30,
)


def matches(key) -> bool:
    return key in ("resources", "extends", "name", "appendCommitMessageToRunName", "lockBehavior")


def apply(key, value, ctx, report) -> None:
    from portover.migrations.azure_pipelines_to_gha import as_list

    if key == "name":
        report.manual(META.id, f"name: {value}",
                      "Azure's build-number format — the closest is `run-name:`; "
                      "$(Date)/$(Rev) tokens have no equivalent (use github.run_number)")
        return
    if key == "extends":
        target = value.get("template") if isinstance(value, dict) else value
        report.manual(META.id, f"extends: {target}",
                      "the pipeline body lives in that template — portover cannot read it; "
                      "convert the template into a reusable workflow (on: workflow_call)")
        return
    if key in ("appendCommitMessageToRunName", "lockBehavior"):
        report.manual(META.id, f"{key}: {value}", "no GHA equivalent")
        return
    if not isinstance(value, dict):
        return
    for entry in as_list(value.get("repositories")):
        if isinstance(entry, dict):
            report.manual(META.id, f"resources.repositories: {entry.get('repository')}",
                          f"add a second checkout step: `uses: actions/checkout@v4` with "
                          f"`repository: {entry.get('name', '<owner>/<repo>')}` (and a token if private)")
    for entry in as_list(value.get("pipelines")):
        if isinstance(entry, dict):
            detail = "use `on: workflow_run` to run after the upstream workflow" if entry.get("trigger") \
                else "download its artifacts with actions/download-artifact and an explicit run-id"
            report.manual(META.id, f"resources.pipelines: {entry.get('pipeline')}", detail)
    for entry in as_list(value.get("containers")):
        if isinstance(entry, dict):
            report.manual(META.id, f"resources.containers: {entry.get('container')}",
                          f"reference the image ({entry.get('image', '?')}) directly in the job's "
                          "`container:` or `services:`")
    for entry in as_list(value.get("webhooks")) + as_list(value.get("packages")):
        if isinstance(entry, dict):
            report.manual(META.id, "resources.webhooks/packages",
                          "use `on: repository_dispatch` for webhooks; packages have no trigger equivalent")
