"""template — step, job and stage templates."""

from portover.core import MappingMeta

SCOPE = "step"

META = MappingMeta(
    id="template",
    directive="- template: steps/build.yml@repo",
    title="Migrate Azure Pipelines templates to GitHub Actions",
    before="""steps:
  - template: templates/build-steps.yml
    parameters:
      buildConfig: Release""",
    after="""steps:
  # a step template is closest to a composite action:
  - uses: ./.github/actions/build-steps
    with:
      buildConfig: Release""",
    notes=(
        "portover only reads the file you point it at, so a template's contents "
        "are NOT in the output — this is always a manual step. The mapping "
        "depends on what the template holds: STEP templates become composite "
        "actions (.github/actions/<name>/action.yml, called with `uses: ./...`), "
        "while JOB and STAGE templates become reusable workflows "
        "(`on: workflow_call`, called with `uses: ./.github/workflows/x.yml`). "
        "Template `parameters:` become the action's `inputs:` in both cases. "
        "An `extends:` template at the top of a pipeline is the whole pipeline's "
        "shape and usually needs rethinking rather than translating."
    ),
    manual=True,
    priority=16,
)


def matches(name) -> bool:
    return name == "template"


def apply(name, item, out, ctx, report) -> None:
    target = str(item.get("template", ""))
    parameters = item.get("parameters") or {}
    detail = ("step template — extract it into a composite action "
              "(.github/actions/<name>/action.yml) and call it with `uses: ./.github/actions/<name>`")
    if parameters:
        detail += f"; its parameters ({', '.join(sorted(map(str, parameters)))}) become the action's inputs"
    report.manual(META.id, f"template: {target}", detail)
    out.append({"run": f"echo 'TODO: port Azure step template {target}'"})
