"""checkout — checkout the repository."""

from portover.core import MappingMeta

SCOPE = "step"

META = MappingMeta(
    id="checkout", directive="- checkout", title="Migrate the CircleCI checkout step",
    before="""steps:
  - checkout""", after="""steps:
  - uses: actions/checkout@v4""",
    notes="A non-default CircleCI checkout path is carried to actions/checkout's `path` input.", priority=10,
)


def matches(name) -> bool:
    return name == "checkout"


def apply(name, value, out, ctx, report) -> None:
    step = {"uses": "actions/checkout@v4"}
    if isinstance(value, dict) and value.get("path"):
        step["with"] = {"path": value["path"]}
    out.append(step)
    report.mapped(META.id, "step: checkout", "actions/checkout@v4")
