"""-r / -c include lines."""

from portover.core import MappingMeta

META = MappingMeta(
    id="include",
    directive="-r file / -c file",
    title="Migrate pip -r includes and -c constraints to uv",
    before="-r base.txt\n-c constraints.txt",
    after="""# includes disappear: uv reads everything from pyproject.toml
[tool.uv]
constraint-dependencies = ["grpcio<1.60"]  # contents of constraints.txt""",
    notes=(
        "uv has no include chain — run portover in each directory or merge the "
        "included files first. `-c` maps to `[tool.uv] constraint-dependencies`, "
        "which takes the *contents* of the constraints file, not its path."
    ),
    priority=10,
)


def matches(line: str) -> bool:
    return line.startswith(("-r ", "--requirement ", "-c ", "--constraint "))


def apply(line: str, ctx, report) -> None:
    flag, _, target = line.partition(" ")
    target = target.strip()
    if flag in ("-c", "--constraint"):
        report.manual(META.id, line,
                      f"copy the specs from {target} into [tool.uv] constraint-dependencies")
    else:
        report.manual(META.id, line,
                      f"inline {target} into pyproject.toml (uv has no -r include chain)")
