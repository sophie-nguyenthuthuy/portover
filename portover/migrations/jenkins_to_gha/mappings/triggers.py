"""triggers — cron, pollSCM, upstream."""

from portover.core import MappingMeta
from portover.migrations.jenkins_to_gha.parser import call_arg

SCOPE = "pipeline"

META = MappingMeta(
    id="triggers",
    directive="triggers { cron / pollSCM / upstream }",
    title="Migrate Jenkins triggers to GitHub Actions on:",
    before="triggers {\n  cron('H 4 * * 1-5')\n  pollSCM('H/5 * * * *')\n}",
    after="""on:
  schedule:
    - cron: "0 4 * * 1-5"
  push: {}""",
    notes=(
        "Jenkins 'H' spreads load by hashing the job name; GHA needs a concrete "
        "value — portover substitutes 0 and flags it. pollSCM is obsolete: GHA "
        "is event-driven, `on: push` replaces polling. upstream(...) maps to "
        "`on: workflow_run` and needs the upstream workflow's name."
    ),
    priority=18,
)


def matches(node) -> bool:
    return node.keyword() == "triggers"


def apply(node, ctx, report) -> None:
    on = ctx.workflow["on"]
    for stmt in node.stmts:
        name = stmt.split("(")[0].strip()
        if name == "cron":
            spec = call_arg(stmt)
            fixed = " ".join("0" if f.startswith("H") and "/" not in f else f.replace("H/", "*/") for f in spec.split())
            on.setdefault("schedule", []).append({"cron": fixed})
            if fixed != spec:
                report.manual(META.id, stmt, f"'H' hash slots replaced: '{spec}' -> '{fixed}' — adjust if you want a different slot")
            else:
                report.mapped(META.id, stmt, f"on.schedule: {fixed}")
        elif name == "pollSCM":
            on.setdefault("push", {})
            report.mapped(META.id, stmt, "polling replaced by event-driven on: push")
        elif name == "upstream":
            report.manual(META.id, stmt, "map to on: workflow_run with the upstream workflow's name")
        else:
            report.manual(META.id, stmt, f"trigger '{name}' has no direct GHA equivalent")
