"""job definitions — every top-level key that is not a pipeline setting."""

from portover.core import MappingMeta

SCOPE = "pipeline"

META = MappingMeta(
    id="jobs",
    directive="<job name>: (any top-level key that is not a pipeline setting)",
    title="Migrate GitLab CI jobs to GitHub Actions jobs",
    before="""unit tests:
  stage: test
  image: python:3.12
  script:
    - pytest -q

.template:          # hidden: a template, never runs
  before_script:
    - pip install -r requirements.txt""",
    after="""jobs:
  unit-tests:
    runs-on: ubuntu-latest
    container: python:3.12
    steps:
      - uses: actions/checkout@v4
      - run: pytest -q""",
    notes=(
        "GitLab has no `jobs:` key — any top-level key that is not a pipeline "
        "setting IS a job, which is why portover claims them here last, after "
        "every other mapping has had its chance. Two conversions happen: job "
        "names are slugged into valid GHA job ids (`unit tests` -> `unit-tests`, "
        "with the original kept as the display `name:`), and jobs whose name "
        "starts with a dot are hidden templates — they are recorded for "
        "`extends:` and never emitted as jobs. Every job starts with "
        "actions/checkout, because GitLab clones the repo for you."
    ),
    priority=90,  # last: everything not claimed above is a job
)


def matches(key) -> bool:
    from portover.migrations.gitlab_ci_to_gha import GLOBAL_KEYS

    return key not in GLOBAL_KEYS


def apply(key, value, ctx, report) -> None:
    from portover.migrations.gitlab_ci_to_gha import as_list, note_ci_vars, scoped, slug
    from portover.migrations.gitlab_ci_to_gha.mappings import extends as extends_map

    name = str(key)
    if not isinstance(value, dict):
        report.unmapped.append(f"{name}: {value!r}")
        return
    if name.startswith("."):
        ctx.templates[name] = value
        report.mapped("extends", f"{name} (template)", "recorded for extends:, not emitted as a job")
        return

    definition = extends_map.resolve(value, ctx, report, job=name)
    jid = slug(name)
    if jid in ctx.jobs:
        jid = f"{jid}-{len(ctx.jobs)}"
    job: dict = {"runs-on": "ubuntu-latest"}
    if jid != name:
        job["name"] = name

    ctx.scripts = {"before": [], "main": [], "after": []}
    ctx.current_jid = jid
    ctx.job_stage[jid] = str(definition.get("stage", "test"))

    merged = _with_defaults(definition, ctx)
    job_maps = scoped("job")
    for field, spec in merged.items():
        if field == "stage":
            continue
        for m in job_maps:
            if m.matches(field):
                m.apply(field, spec, job, ctx, report)
                break
        else:
            report.unmapped.append(f"{name}: {field}")

    for bucket in ("before", "main", "after"):
        for command in ctx.scripts[bucket]:
            note_ci_vars(command, ctx)

    steps = [{"uses": "actions/checkout@v4"}]
    steps.extend(job.pop("_pre_steps", []))
    steps.extend({"run": c} for c in ctx.scripts["before"])
    steps.extend({"run": c} for c in ctx.scripts["main"])
    steps.extend({"run": c} for c in ctx.scripts["after"])
    steps.extend(job.pop("_post_steps", []))
    job["steps"] = steps

    if not ctx.scripts["main"] and not any(s.get("uses") != "actions/checkout@v4" for s in steps):
        report.manual(META.id, name, "job has no script — add its commands by hand")

    ctx.jobs[jid] = job
    ctx.job_order.append(jid)
    report.mapped(META.id, name, f"job '{jid}' (stage {ctx.job_stage[jid]})")


def _with_defaults(definition: dict, ctx) -> dict:
    """Apply pipeline defaults the job did not override, preserving field order."""
    merged = dict(definition)
    for field, spec in ctx.defaults.items():
        merged.setdefault(field, spec)
    return merged
