"""jobs — job definitions become GHA job dicts."""

from portover.core import MappingMeta

SCOPE = "pipeline"

META = MappingMeta(
    id="jobs",
    directive="jobs: <name>: steps: [...]",
    title="Migrate CircleCI jobs to GitHub Actions jobs",
    before="""jobs:
  test:
    docker:
      - image: cimg/python:3.12
    steps:
      - checkout
      - run: pytest -q""",
    after="""jobs:
  test:
    runs-on: ubuntu-latest
    container: cimg/python:3.12
    steps:
      - uses: actions/checkout@v4
      - run: pytest -q""",
    notes=(
        "A CircleCI job is only a definition — the `workflows:` block decides "
        "whether and when it runs. GHA jobs are both at once, so portover "
        "converts the definitions here and lets the workflows mapping emit them "
        "with needs/if attached. Job names are slugged to valid GHA job ids "
        "(`build-and-test`, not `build_and test`)."
    ),
    priority=40,
)


def matches(key) -> bool:
    return key == "jobs"


def apply(key, value, ctx, report) -> None:
    from portover.migrations.circleci_to_gha import convert_steps, scoped, slug, CircleCiToGha

    if not isinstance(value, dict):
        return
    job_maps = scoped(CircleCiToGha.package, "job")
    for name, definition in value.items():
        definition = definition if isinstance(definition, dict) else {}
        jid = slug(name)
        ctx.job_names[str(name)] = jid
        ctx.job_raw[jid] = definition
        job: dict = {"runs-on": "ubuntu-latest"}
        for k, v in definition.items():
            if k == "steps":
                continue
            for m in job_maps:
                if m.matches(k):
                    m.apply(k, v, job, ctx, report)
                    break
            else:
                report.unmapped.append(f"jobs.{name}: {k}")
        job["steps"] = convert_steps(definition.get("steps") or [], ctx, report)
        if not job["steps"]:
            report.manual(META.id, f"jobs.{name}", "job has no convertible steps — add its commands by hand")
        ctx.job_defs[jid] = job
        report.mapped(META.id, f"jobs.{name}", f"job '{jid}' ({len(job['steps'])} steps)")
