"""trigger — starting another pipeline."""

from portover.core import MappingMeta

SCOPE = "structure"

META = MappingMeta(
    id="trigger",
    directive="- trigger: other-pipeline / build / async",
    title="Migrate Buildkite trigger steps to GitHub Actions",
    before="""- trigger: deploy-pipeline
  label: Deploy
  async: false
  build:
    branch: main
    env:
      RELEASE: "true\"""",
    after="""deploy:
  uses: ./.github/workflows/deploy.yml
  with:
    RELEASE: "true"
  secrets: inherit""",
    notes=(
        "A trigger step becomes a reusable-workflow call, and the job then "
        "uses `uses:` INSTEAD of `runs-on`/`steps` — the called workflow must "
        "declare `on: workflow_call`. The `async:` flag decides which shape "
        "fits: `async: false` (wait for the triggered build) is exactly a "
        "workflow call, while `async: true` (fire and forget) has no calling "
        "equivalent and is closer to `repository_dispatch` with a token. "
        "`build.env` becomes the called workflow's `with:` inputs, which must "
        "be declared there — environment variables do not cross the boundary "
        "on their own."
    ),
    manual=True,
    priority=48,
)


def matches(key) -> bool:
    return key == "trigger"


def build(entry: dict, ctx, report, *, index: int) -> tuple:
    from portover.migrations.buildkite_to_gha import slug

    target = str(entry.get("trigger"))
    label = str(entry.get("label") or target)
    jid = slug(entry.get("key") or label)
    while jid in ctx.jobs:
        jid = f"{jid}-{index}"

    detail = (f"replace this job with `uses: ./.github/workflows/{slug(target)}.yml` "
              "(plus `secrets: inherit`), and add `on: workflow_call` to that workflow")
    if entry.get("async"):
        detail = ("`async: true` fires and forgets — a workflow call always waits, so use "
                  "`repository_dispatch` (or the gh CLI with a token) instead")
    build_spec = entry.get("build") if isinstance(entry.get("build"), dict) else {}
    if build_spec.get("env"):
        detail += f"; its build.env ({', '.join(sorted(map(str, build_spec['env'])))}) become `with:` inputs"
    report.manual(META.id, f"trigger: {target}", detail)

    job: dict = {"runs-on": "ubuntu-latest",
                 "steps": [{"run": f"echo 'TODO: port Buildkite trigger of {target}'"}]}
    if entry.get("depends_on"):
        from portover.migrations.buildkite_to_gha.mappings import depends_on as depends_map

        needs = depends_map.resolve(entry["depends_on"], ctx, report)
        if needs:
            job["needs"] = needs if len(needs) > 1 else needs[0]
            job["_explicit_needs"] = True
    return jid, job
