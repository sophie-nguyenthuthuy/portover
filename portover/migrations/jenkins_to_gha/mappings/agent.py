"""agent — where the pipeline runs."""

from portover.core import MappingMeta
from portover.migrations.jenkins_to_gha.parser import call_arg

SCOPE = "pipeline"

META = MappingMeta(
    id="agent",
    directive="agent any / agent { label } / agent { docker }",
    title="Migrate Jenkins agent to GitHub Actions runs-on",
    before="agent { docker { image 'python:3.12' } }",
    after="""jobs:
  build:
    runs-on: ubuntu-latest
    container: python:3.12""",
    notes=(
        "`agent any` -> runs-on: ubuntu-latest. `label 'x'` -> runs-on: "
        "[self-hosted, x] (register your Jenkins nodes as self-hosted runners). "
        "`docker { image }` -> container:. `dockerfile` has no direct equivalent "
        "— build the image in a step or prebuild it to a registry."
    ),
    priority=10,
)


def matches(node) -> bool:
    return node.keyword() == "agent"


def apply(node, ctx, report) -> None:
    header_rest = node.header.split(None, 1)[1] if " " in node.header else ""
    if header_rest in ("any", "none"):
        report.mapped(META.id, node.header, f"runs-on: {ctx.runs_on}")
        return
    label = node.child("label") if node.children else None
    docker = node.child("docker") if node.children else None
    for stmt in node.stmts:
        if stmt.startswith("label"):
            ctx.runs_on = ["self-hosted", call_arg(stmt)]
            report.mapped(META.id, node.header, f"runs-on: {ctx.runs_on} (self-hosted runner)")
            return
    if label:
        ctx.runs_on = ["self-hosted", call_arg(label.header)]
        report.mapped(META.id, node.header, f"runs-on: {ctx.runs_on} (self-hosted runner)")
    elif docker:
        image = next((s for s in docker.stmts if s.startswith("image")), None)
        if image:
            ctx.container = call_arg(image)
            report.mapped(META.id, node.header, f"container: {ctx.container}")
    elif node.child("dockerfile") or any(s.startswith("dockerfile") for s in node.stmts):
        report.manual(META.id, node.header,
                      "agent { dockerfile } — prebuild the image (docker/build-push-action) and use container:")
    else:
        report.mapped(META.id, node.header, f"runs-on: {ctx.runs_on}")
