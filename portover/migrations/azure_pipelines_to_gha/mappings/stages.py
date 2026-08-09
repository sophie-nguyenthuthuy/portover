"""stages — the outermost level of the Azure pipeline tree."""

from portover.core import MappingMeta

SCOPE = "pipeline"

META = MappingMeta(
    id="stages",
    directive="stages: [{stage, dependsOn, condition, jobs}]",
    title="Migrate Azure Pipelines stages to GitHub Actions",
    before="""stages:
  - stage: Build
    jobs:
      - job: compile
        steps: [...]
  - stage: Deploy
    dependsOn: Build
    condition: succeeded()
    jobs:
      - job: ship
        steps: [...]""",
    after="""jobs:
  compile:
    steps: [...]
  ship:
    needs: compile        # inherited from the stage dependency
    if: success()
    steps: [...]""",
    notes=(
        "GHA has no stage level, so stages are dissolved into their jobs. The "
        "ordering is preserved by giving each stage's entry jobs a `needs:` on "
        "every job of the stages it depends on — and remember Azure stages are "
        "sequential BY DEFAULT, so a stage with no `dependsOn` still waits for "
        "the previous one (`dependsOn: []` is how you opt out). A stage-level "
        "`condition:` is copied onto each job in that stage, and a stage-level "
        "`variables:` block becomes those jobs' env. Job ids only get a stage "
        "prefix when two stages reuse the same job name."
    ),
    priority=40,
)


def matches(key) -> bool:
    return key == "stages"


def apply(key, value, ctx, report) -> None:
    from portover.migrations.azure_pipelines_to_gha import as_list, slug
    from portover.migrations.azure_pipelines_to_gha.expr import translate
    from portover.migrations.azure_pipelines_to_gha.mappings import jobs as jobs_map

    stages = [s for s in as_list(value) if isinstance(s, dict)]
    previous = None
    for stage in stages:
        name = str(stage.get("stage") or stage.get("displayName") or f"stage{len(ctx.stage_order)}")
        sid = slug(name)
        ctx.stage_order.append(sid)
        ctx.stage_jobs.setdefault(sid, [])

        depends = stage.get("dependsOn")
        if depends is None:
            parents = [previous] if previous else []  # sequential by default
        else:
            parents = [slug(str(d)) for d in as_list(depends)]
        ctx.stage_depends[sid] = [p for p in parents if p]

        condition = None
        if stage.get("condition") is not None:
            condition = translate(stage["condition"], report, META.id)
            if condition:
                report.mapped(META.id, f"stage {name} condition", condition)

        stage_env = stage.get("variables")
        if "template" in stage:
            report.manual(META.id, f"stage {name}: template",
                          "stage template — inline it or extract a reusable workflow (on: workflow_call)")

        for job in as_list(stage.get("jobs")):
            if isinstance(job, dict):
                jobs_map.build(job, ctx, report, stage=sid,
                               stage_condition=condition, stage_variables=stage_env)
        report.mapped(META.id, f"stage: {name}",
                      f"{len(ctx.stage_jobs[sid])} job(s)" + (f", needs {ctx.stage_depends[sid]}" if ctx.stage_depends[sid] else ""))
        previous = sid
