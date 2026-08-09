"""tools — jdk/nodejs/maven/go tool installers."""

import re

from portover.core import MappingMeta
from portover.migrations.jenkins_to_gha.parser import call_arg

SCOPE = "pipeline"

META = MappingMeta(
    id="tools",
    directive="tools { jdk / nodejs / maven / go }",
    title="Migrate Jenkins tools blocks to GitHub Actions setup-* actions",
    before="tools {\n  jdk 'jdk17'\n  nodejs 'node20'\n}",
    after="""steps:
  - uses: actions/setup-java@v4
    with: { distribution: temurin, java-version: "17" }
  - uses: actions/setup-node@v4
    with: { node-version: "20" }""",
    notes=(
        "Jenkins tool names are labels configured on the controller; portover "
        "extracts the version number from the label — check it. maven: "
        "ubuntu-latest runners ship mvn; setup-java handles the JDK."
    ),
    priority=14,
)

_ACTIONS = {
    "jdk": ("actions/setup-java@v4", "java-version", {"distribution": "temurin"}),
    "nodejs": ("actions/setup-node@v4", "node-version", {}),
    "go": ("actions/setup-go@v5", "go-version", {}),
    "python": ("actions/setup-python@v5", "python-version", {}),
}


def matches(node) -> bool:
    return node.keyword() == "tools"


def apply(node, ctx, report) -> None:
    for stmt in node.stmts:
        tool = stmt.split()[0]
        label = call_arg(stmt)
        version = ".".join(re.findall(r"\d+", label)) or label
        if tool in _ACTIONS:
            action, key, extra = _ACTIONS[tool]
            ctx.setup_steps.append({"uses": action, "with": {**extra, key: version}})
            report.mapped(META.id, stmt, f"{action} ({key}: {version})")
        elif tool == "maven":
            report.mapped(META.id, stmt, "mvn is preinstalled on ubuntu-latest; setup-java covers the JDK")
        else:
            report.manual(META.id, stmt, f"no setup action mapped for tool '{tool}' — install it in a run step")
