"""Jenkinsfile (declarative) -> GitHub Actions workflow.

Driver: parse the Jenkinsfile, dispatch each directive under `pipeline { }` to
the mapping that claims it (SCOPE = "pipeline"), let the stages mapping build
jobs, and render .github/workflows/ci.yml. Step statements inside `steps { }`
are dispatched to SCOPE = "step" mappings via convert_steps().
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from portover.core import Migration, Report
from portover.emit import yaml_dump
from portover.migrations.jenkins_to_gha.parser import Node, parse


@dataclass
class GhaContext:
    workflow: dict = field(default_factory=dict)
    runs_on: str = "ubuntu-latest"
    container: str | None = None
    env: dict = field(default_factory=dict)
    setup_steps: list = field(default_factory=list)  # from tools {}, prepended per job
    job_order: list[str] = field(default_factory=list)
    timeout: int | None = None


def slug(name: str) -> str:
    s = "".join(c if c.isalnum() else "-" for c in name.lower()).strip("-")
    return s or "job"


class JenkinsToGha(Migration):
    id = "jenkins-to-gha"
    source = "Jenkinsfile (declarative pipeline)"
    target = ".github/workflows/*.yml (GitHub Actions)"
    package = "portover.migrations.jenkins_to_gha"

    def detect(self, root) -> list[str]:
        root = Path(root)
        return [f for f in ("Jenkinsfile", "jenkinsfile", "Jenkinsfile.groovy") if (root / f).exists()]

    def run(self, root) -> Report:
        root = Path(root)
        report = Report(self.id)
        fname = self.detect(root)[0]
        tree = parse((root / fname).read_text())
        pipeline = tree.child("pipeline")
        if pipeline is None:
            report.manual("scripted", fname,
                          "no `pipeline { }` block found — scripted (Groovy) pipelines need a hand rewrite")
            return report

        ctx = GhaContext(workflow={"name": "CI", "on": {}, "jobs": {}})
        mappings = [m for m in self.mappings() if getattr(m, "SCOPE", "pipeline") == "pipeline"]
        items = [Node(s) for s in pipeline.stmts] + pipeline.children
        # directives are order-independent in Jenkins; honour mapping priority
        # so agent/environment/tools configure ctx before stages builds jobs
        for m in mappings:
            for node in [it for it in items if m.matches(it)]:
                m.apply(node, ctx, report)
                items.remove(node)
        for node in items:
            if node.header:
                report.unmapped.append(f"{fname}: {node.header}")

        if not ctx.workflow["on"]:
            ctx.workflow["on"] = {"push": {"branches": ["main"]}, "pull_request": {}}
        if ctx.env:
            ctx.workflow["env"] = ctx.env
        ctx.workflow["jobs"] = ctx.workflow.pop("jobs")  # keep jobs last
        report.outputs[".github/workflows/ci.yml"] = yaml_dump(ctx.workflow) + "\n"
        return report


def step_mappings():
    from portover.core import load_mappings

    return [m for m in load_mappings(JenkinsToGha.package) if getattr(m, "SCOPE", "") == "step"]


def convert_steps(node: Node, ctx: GhaContext, report: Report) -> list[dict]:
    """Convert the contents of a steps{}/post-condition{} block to GHA steps."""
    steps: list[dict] = []
    maps = step_mappings()
    items: list = list(node.stmts)
    for child in node.children:
        if child.keyword() in ("script", "dir", "withEnv", "timeout", "retry"):
            items.extend(child.stmts)  # flatten wrappers, keep their statements
            if child.keyword() != "script":
                report.manual("steps", child.header, f"`{child.keyword()}` wrapper flattened — re-add its semantics by hand")
        else:
            items.append(child)
    for it in items:
        stmt = it if isinstance(it, str) else it.header
        for m in maps:
            if m.matches(stmt):
                m.apply(stmt, steps, ctx, report)
                break
        else:
            report.unmapped.append(f"step: {stmt}")
    return steps


def new_job(ctx: GhaContext, *, needs: list[str] | None = None) -> dict:
    job: dict = {"runs-on": ctx.runs_on}
    if ctx.container:
        job["container"] = ctx.container
    if needs:
        job["needs"] = needs if len(needs) > 1 else needs[0]
    if ctx.timeout:
        job["timeout-minutes"] = ctx.timeout
    job["steps"] = [{"uses": "actions/checkout@v4"}] + [dict(s) for s in ctx.setup_steps]
    return job


MIGRATION = JenkinsToGha()
