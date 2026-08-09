"""block / input — manual gates and prompts."""

from portover.core import MappingMeta

SCOPE = "structure"

META = MappingMeta(
    id="block-input",
    directive="- block: / - input: with fields / prompt",
    title="Migrate Buildkite block and input steps to GitHub Actions",
    before="""- block: ":rocket: Release?"
  key: gate
  prompt: Ship to production?
  fields:
    - select: Environment
      key: env
      options:
        - {label: Staging, value: staging}
        - {label: Production, value: production}""",
    after="""gate:
  environment: approval      # add required reviewers in repo settings
  steps:
    - run: echo "approval gate"
# the fields have no in-run equivalent — collect them as
# workflow_dispatch inputs instead:
on:
  workflow_dispatch:
    inputs:
      env:
        type: choice
        options: [staging, production]""",
    notes=(
        "A block step pauses a running build until someone clicks, and GHA's "
        "equivalent is an Environment with required reviewers — same effect, "
        "configured in repository settings rather than YAML. Where the two "
        "genuinely part ways is `fields:`: Buildkite collects input DURING the "
        "run and later steps read it with `buildkite-agent meta-data get`, "
        "while GHA can only take inputs BEFORE the run starts "
        "(workflow_dispatch). So a block step with fields has to be "
        "restructured — usually into a manually triggered workflow — and "
        "portover reports the fields it found so you can transplant them."
    ),
    priority=46,
)


def matches(key) -> bool:
    return key in ("block", "input")


def build(entry: dict, ctx, report, *, index: int) -> tuple:
    from portover.migrations.buildkite_to_gha import as_list, slug

    from portover.migrations.buildkite_to_gha import _clean_label

    kind = "block" if "block" in entry else "input"
    label = _clean_label(entry.get(kind) or entry.get("label") or f"{kind} {index}")
    jid = slug(entry.get("key") or label)
    while jid in ctx.jobs:
        jid = f"{jid}-{index}"

    job: dict = {"runs-on": "ubuntu-latest", "environment": "approval",
                 "steps": [{"run": f'echo "{kind} gate: {label}"'}]}
    if entry.get("if"):
        from portover.migrations.buildkite_to_gha.expr import translate

        condition = translate(entry["if"], report, META.id)
        if condition:
            job["if"] = condition
    if entry.get("depends_on"):
        from portover.migrations.buildkite_to_gha.mappings import depends_on as depends_map

        needs = depends_map.resolve(entry["depends_on"], ctx, report)
        if needs:
            job["needs"] = needs if len(needs) > 1 else needs[0]
            job["_explicit_needs"] = True

    report.manual(META.id, f"{kind}: {label}",
                  "create an Environment named 'approval' with required reviewers — "
                  "that is what pauses the run for a click")
    fields = as_list(entry.get("fields"))
    if fields:
        names = [str(f.get("key") or f.get("text") or f.get("select"))
                 for f in fields if isinstance(f, dict)]
        report.manual(META.id, f"{kind} fields: {names}",
                      "GHA cannot collect input mid-run — move these to "
                      "`on: workflow_dispatch: inputs:` and read them as ${{ inputs.<name> }}")
    return jid, job
