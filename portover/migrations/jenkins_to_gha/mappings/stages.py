"""stages — the pipeline structure itself: stages become jobs."""

from portover.core import MappingMeta
from portover.migrations.jenkins_to_gha.parser import unquote
from portover.migrations.jenkins_to_gha.mappings import environment as env_map
from portover.migrations.jenkins_to_gha.mappings import when as when_map

SCOPE = "pipeline"

META = MappingMeta(
    id="stages",
    directive="stages { stage('X') { steps { ... } } }",
    title="Migrate Jenkins stages to GitHub Actions jobs",
    before="""stages {
  stage('Build') { steps { sh 'make build' } }
  stage('Test')  { steps { sh 'make test' } }
}""",
    after="""jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: make build
  test:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: make test""",
    notes=(
        "Each stage becomes a job chained with needs: to keep Jenkins' "
        "sequential order. Jenkins stages share a workspace; GHA jobs do NOT — "
        "hand artifacts between jobs with upload-/download-artifact, or merge "
        "trivially-small stages into one job's steps. Declarative pipelines "
        "check out code implicitly, so every job starts with actions/checkout."
    ),
    priority=40,
)


def matches(node) -> bool:
    return node.keyword() == "stages"


def stage_name(header: str) -> str:
    inner = header.split("(", 1)[1].rsplit(")", 1)[0] if "(" in header else header
    return unquote(inner)


def apply(node, ctx, report) -> None:
    from portover.migrations.jenkins_to_gha import convert_steps, new_job, slug

    prev: list[str] = []
    for stage in node.children:
        if stage.keyword() != "stage":
            continue
        par = stage.child("parallel")
        members = [c for c in par.children if c.keyword() == "stage"] if par else [stage]
        if par:
            report.mapped("parallel", stage.header, f"{len(members)} sibling jobs, shared needs")
        current: list[str] = []
        for st in members:
            jid = slug(stage_name(st.header))
            job = new_job(ctx, needs=prev or None)
            when = st.child("when")
            if when is not None:
                cond = when_map.to_if(when, report)
                if cond:
                    job["if"] = cond
            env_node = st.child("environment")
            if env_node is not None:
                job["env"] = env_map.parse_env(env_node, report)
            steps_node = st.child("steps")
            if steps_node is not None:
                job["steps"].extend(convert_steps(steps_node, ctx, report))
            post = st.child("post")
            if post is not None:
                for cond_block in post.children:
                    cond = {"always": "always()", "success": "success()", "failure": "failure()",
                            "cleanup": "always()", "unstable": "failure()"}.get(cond_block.keyword(), "always()")
                    for s in convert_steps(cond_block, ctx, report):
                        job["steps"].append({"if": cond, **s})
            ctx.workflow["jobs"][jid] = job
            ctx.job_order.append(jid)
            current.append(jid)
            report.mapped(META.id, st.header, f"job '{jid}'" + (f" needs {prev}" if prev else ""))
        prev = current
