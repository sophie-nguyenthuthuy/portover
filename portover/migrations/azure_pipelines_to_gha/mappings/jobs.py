"""jobs — job definitions (and the bare `steps:` shorthand)."""

from portover.core import MappingMeta

SCOPE = "pipeline"

META = MappingMeta(
    id="jobs",
    directive="jobs: [{job, dependsOn, condition, steps}] / steps:",
    title="Migrate Azure Pipelines jobs to GitHub Actions jobs",
    before="""jobs:
  - job: test
    displayName: Run tests
    dependsOn: build
    steps:
      - script: pytest -q""",
    after="""jobs:
  test:
    name: Run tests
    needs: build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pytest -q""",
    notes=(
        "`dependsOn` becomes `needs` directly — unlike stages, Azure jobs run "
        "in PARALLEL by default, matching GHA, so only explicit dependencies "
        "carry over. `displayName` becomes `name`. A pipeline can also skip the "
        "jobs level entirely and write bare `steps:`, which becomes a single "
        "job called `build`. Deployment jobs (`- deployment:` with a "
        "`strategy: runOnce`) are converted as ordinary jobs pointing at a GHA "
        "Environment, since GHA has no separate deployment-job type."
    ),
    priority=42,
)


def matches(key) -> bool:
    return key in ("jobs", "steps")


def apply(key, value, ctx, report) -> None:
    from portover.migrations.azure_pipelines_to_gha import as_list

    if key == "steps":
        build({"job": "build", "steps": value}, ctx, report, stage=None)
        report.mapped(META.id, "steps: (no jobs level)", "single job 'build'")
        return
    for job in as_list(value):
        if isinstance(job, dict):
            build(job, ctx, report, stage=None)


def build(definition: dict, ctx, report, *, stage=None,
          stage_condition=None, stage_variables=None) -> str:
    """Convert one Azure job definition into a GHA job."""
    from portover.migrations.azure_pipelines_to_gha import as_list, scoped, slug
    from portover.migrations.azure_pipelines_to_gha.mappings import pool as pool_map
    from portover.migrations.azure_pipelines_to_gha.mappings import steps as steps_map

    source_name = str(definition.get("job") or definition.get("deployment")
                      or definition.get("displayName") or f"job{len(ctx.job_order)}")
    jid = slug(source_name)
    if jid in ctx.jobs and stage:
        jid = f"{stage}-{jid}"
    while jid in ctx.jobs:
        jid = f"{jid}-{len(ctx.job_order)}"

    job: dict = {"runs-on": "ubuntu-latest", "_source_name": source_name}
    if definition.get("displayName"):
        job["name"] = str(definition["displayName"])
    if ctx.default_pool:
        pool_map.resolve(ctx.default_pool, job, ctx, report)

    ctx.current_jid = jid
    ctx.matrix_vars = set()
    ctx.job_stage[jid] = stage
    if stage:
        ctx.stage_jobs.setdefault(stage, []).append(jid)
    ctx.job_depends[jid] = [str(d) for d in as_list(definition.get("dependsOn"))]

    if stage_variables:
        _variables(stage_variables, job, ctx, report)
    if stage_condition:
        job["if"] = stage_condition

    if definition.get("deployment"):
        report.manual(META.id, f"deployment: {source_name}",
                      "a deployment job — converted as a normal job; point it at a GHA Environment "
                      "for approvals and deployment history")
        environment = definition.get("environment")
        if environment:
            name = environment.get("name") if isinstance(environment, dict) else environment
            job["environment"] = str(name)

    step_items = definition.get("steps")
    if step_items is None and isinstance(definition.get("strategy"), dict):
        step_items = _runonce_steps(definition["strategy"], report, source_name)

    job_maps = scoped("job")
    for field, spec in definition.items():
        if field in ("job", "deployment", "displayName", "steps", "dependsOn", "environment"):
            continue
        if field == "strategy" and step_items is not None and "steps" not in definition:
            continue  # runOnce wrapper, already unwrapped
        for m in job_maps:
            if m.matches(field):
                m.apply(field, spec, job, ctx, report)
                break
        else:
            report.unmapped.append(f"{source_name}: {field}")

    job["steps"] = steps_map.convert(step_items, ctx, report)
    ctx.jobs[jid] = job
    ctx.job_order.append(jid)
    report.mapped(META.id, f"job: {source_name}", f"job '{jid}' ({len(job['steps'])} steps)")
    return jid


def _variables(spec, job, ctx, report) -> None:
    from portover.migrations.azure_pipelines_to_gha.mappings import job_variables

    job_variables.apply("variables", spec, job, ctx, report)


def _runonce_steps(strategy: dict, report, name: str):
    """Unwrap a deployment job's strategy: runOnce: deploy: steps:."""
    for kind in ("runOnce", "rolling", "canary"):
        phase = strategy.get(kind)
        if isinstance(phase, dict):
            if kind != "runOnce":
                report.manual(META.id, f"{name}: strategy.{kind}",
                              f"{kind} deployment strategy has no GHA equivalent — converted as a single run")
            deploy = phase.get("deploy")
            if isinstance(deploy, dict):
                return deploy.get("steps")
    return None
