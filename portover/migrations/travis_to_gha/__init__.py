""".travis.yml (Travis CI) -> GitHub Actions workflow.

Driver: parse the YAML with miniyaml, hand each top-level key to the mapping
that claims it, then assemble a single `test` job (the Travis model: one job
definition fanned out by a matrix) and render .github/workflows/ci.yml.
"""

from __future__ import annotations

import shlex
from dataclasses import dataclass, field
from pathlib import Path

from portover.core import Migration, Report
from portover.emit import yaml_dump
from portover.miniyaml import MiniYamlError, parse

# Travis phase -> (GHA step condition, order)
PHASES = [
    ("before_install", None),
    ("install", None),
    ("before_script", None),
    ("script", None),
    ("after_success", "success()"),
    ("after_failure", "failure()"),
    ("after_script", "always()"),
]


@dataclass
class TravisContext:
    workflow: dict = field(default_factory=dict)
    runs_on: object = "ubuntu-latest"
    matrix: dict = field(default_factory=dict)
    matrix_include: list = field(default_factory=list)
    matrix_exclude: list = field(default_factory=list)
    env: dict = field(default_factory=dict)
    env_rows: list = field(default_factory=list)  # Travis env matrix rows (strings)
    services: dict = field(default_factory=dict)
    setup_steps: list = field(default_factory=list)  # setup-python etc
    pre_steps: list = field(default_factory=list)  # apt installs etc
    phases: dict = field(default_factory=dict)  # phase name -> [commands]
    fetch_depth: object = None
    language: str = ""


def parse_env_vars(row: str) -> dict:
    out = {}
    for tok in shlex.split(row):
        if "=" in tok:
            k, _, v = tok.partition("=")
            out[k] = v
    return out


class TravisToGha(Migration):
    id = "travis-to-gha"
    source = ".travis.yml (Travis CI)"
    target = ".github/workflows/*.yml (GitHub Actions)"
    package = "portover.migrations.travis_to_gha"

    def detect(self, root) -> list[str]:
        return [".travis.yml"] if (Path(root) / ".travis.yml").exists() else []

    def run(self, root) -> Report:
        root = Path(root)
        report = Report(self.id)
        try:
            doc = parse((root / ".travis.yml").read_text())
        except MiniYamlError as e:
            report.manual("parse", ".travis.yml",
                          f"file uses YAML features portover's reader skips ({e}) — simplify it or migrate by hand")
            return report
        if not isinstance(doc, dict):
            report.manual("parse", ".travis.yml", "expected a top-level mapping")
            return report

        ctx = TravisContext(workflow={"name": "CI", "on": {}, "jobs": {}})
        mappings = self.mappings()
        keys = list(doc)
        for m in mappings:
            for key in [k for k in keys if m.matches(k)]:
                m.apply(key, doc[key], ctx, report)
                keys.remove(key)
        for key in keys:
            report.unmapped.append(f".travis.yml: {key}")

        self._assemble(ctx, report)
        report.outputs[".github/workflows/ci.yml"] = yaml_dump(ctx.workflow) + "\n"
        return report

    def _assemble(self, ctx: TravisContext, report: Report) -> None:
        if not ctx.workflow["on"]:
            ctx.workflow["on"] = {"push": {"branches": ["main"]}, "pull_request": {}}

        checkout: dict = {"uses": "actions/checkout@v4"}
        if ctx.fetch_depth is not None:
            checkout["with"] = {"fetch-depth": ctx.fetch_depth}
        steps: list = [checkout] + ctx.setup_steps + ctx.pre_steps

        if len(ctx.env_rows) == 1:
            ctx.env.update(parse_env_vars(ctx.env_rows[0]))
        elif len(ctx.env_rows) > 1:
            ctx.matrix["env"] = ctx.env_rows
            steps.append({"name": "Export env matrix row",
                          "run": 'tr " " "\\n" <<< "${{ matrix.env }}" >> "$GITHUB_ENV"'})

        for phase, cond in PHASES:
            for cmd in ctx.phases.get(phase, []):
                step: dict = {"run": cmd}
                if cond:
                    step = {"if": cond, "run": cmd}
                steps.append(step)
        if not ctx.phases.get("script"):
            report.manual("script", "script",
                          "no `script:` phase found — add your test command as a run step")

        job: dict = {"runs-on": ctx.runs_on}
        strategy = {}
        if ctx.matrix:
            strategy["matrix"] = ctx.matrix
        if ctx.matrix_include:
            strategy.setdefault("matrix", {})["include"] = ctx.matrix_include
        if ctx.matrix_exclude:
            strategy.setdefault("matrix", {})["exclude"] = ctx.matrix_exclude
        if strategy:
            job["strategy"] = strategy
        if ctx.services:
            job["services"] = ctx.services
        if ctx.env:
            job["env"] = ctx.env
        job["steps"] = steps
        ctx.workflow["jobs"]["test"] = job


MIGRATION = TravisToGha()
