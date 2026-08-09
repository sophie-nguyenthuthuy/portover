"""executor — resolve a reusable CircleCI executor into a job."""

from portover.core import MappingMeta

SCOPE = "job"

META = MappingMeta(
    id="executor",
    directive="executor: <name>",
    title="Migrate a CircleCI reusable executor reference",
    before="executor: python-executor",
    after="""runs-on: ubuntu-latest
container: cimg/python:3.12""",
    notes="The named executor is expanded inline because GHA jobs cannot refer to a shared executor block.",
    priority=5,
)


def matches(key) -> bool:
    return key == "executor"


def apply(key, value, job, ctx, report) -> None:
    from portover.migrations.circleci_to_gha import scoped, CircleCiToGha

    name = value.get("name") if isinstance(value, dict) else value
    definition = ctx.executors.get(name)
    if not definition:
        report.manual(META.id, f"executor: {name}", "named executor definition was not found")
        return
    for k, v in definition.items():
        for mapping in scoped(CircleCiToGha.package, "job"):
            if mapping.META.id != META.id and mapping.matches(k):
                mapping.apply(k, v, job, ctx, report)
                break
        else:
            report.unmapped.append(f"executor.{name}: {k}")
    if isinstance(value, dict) and len(value) > 1:
        report.manual(META.id, f"executor: {name}",
                      "executor parameters need substitution in the expanded definition")
    report.mapped(META.id, f"executor: {name}", "expanded inline")
