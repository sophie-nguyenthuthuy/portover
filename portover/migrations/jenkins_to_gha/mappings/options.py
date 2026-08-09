"""options — timeout, buildDiscarder, disableConcurrentBuilds, timestamps."""

from portover.core import MappingMeta
from portover.migrations.jenkins_to_gha.parser import kwargs

SCOPE = "pipeline"

META = MappingMeta(
    id="options",
    directive="options { timeout / disableConcurrentBuilds / buildDiscarder }",
    title="Migrate Jenkins options to GitHub Actions",
    before="options {\n  timeout(time: 30, unit: 'MINUTES')\n  disableConcurrentBuilds()\n}",
    after="""concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: false
jobs:
  build:
    timeout-minutes: 30""",
    notes=(
        "timeout -> per-job timeout-minutes. disableConcurrentBuilds -> a "
        "workflow concurrency group. buildDiscarder/logRotator has no YAML "
        "equivalent — retention lives in repo Settings > Actions. timestamps() "
        "is the GHA default and is dropped."
    ),
    priority=16,
)

_UNIT_MIN = {"SECONDS": 1 / 60, "MINUTES": 1, "HOURS": 60}


def matches(node) -> bool:
    return node.keyword() == "options"


def apply(node, ctx, report) -> None:
    for stmt in node.stmts:
        name = stmt.split("(")[0].strip()
        if name == "timeout":
            kw = kwargs(stmt)
            minutes = int(float(kw.get("time", 60)) * _UNIT_MIN.get(kw.get("unit", "MINUTES"), 1)) or 1
            ctx.timeout = minutes
            report.mapped(META.id, stmt, f"timeout-minutes: {minutes}")
        elif name == "disableConcurrentBuilds":
            ctx.workflow["concurrency"] = {
                "group": "${{ github.workflow }}-${{ github.ref }}",
                "cancel-in-progress": False,
            }
            report.mapped(META.id, stmt, "concurrency group")
        elif name == "timestamps":
            report.mapped(META.id, stmt, "dropped — GHA logs are timestamped by default")
        elif name == "buildDiscarder":
            report.manual(META.id, stmt, "log/artifact retention is set in repo Settings > Actions, not YAML")
        else:
            report.manual(META.id, stmt, f"option '{name}' has no direct GHA equivalent")
