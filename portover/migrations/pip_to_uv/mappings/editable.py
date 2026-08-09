"""-e / --editable installs."""

from pathlib import PurePosixPath

from portover.core import MappingMeta
from portover.migrations.pip_to_uv import req_name

META = MappingMeta(
    id="editable",
    directive="-e / --editable",
    title="Migrate pip -e (editable installs) to uv",
    before="-e ./libs/mypkg",
    after="""dependencies = ["mypkg"]

[tool.uv.sources]
mypkg = { path = "libs/mypkg", editable = true }""",
    notes=(
        "uv splits the dependency (name in [project]) from where it comes from "
        "([tool.uv.sources]). `-e .` (the project itself) is simply not needed: "
        "uv always installs the current project editable inside its venv."
    ),
    priority=10,
)


def matches(line: str) -> bool:
    return line.startswith(("-e ", "--editable "))


def apply(line: str, ctx, report) -> None:
    target = line.split(None, 1)[1].strip()
    if target in (".", "./"):
        report.mapped(META.id, line, "`-e .` dropped — uv installs the project editable by default")
        return
    if target.startswith(("git+", "hg+", "svn+", "bzr+")) or "://" in target:
        report.manual(META.id, line, "editable VCS install: add a git source, editable clones need `uv pip install -e` manually")
        return
    name = req_name(PurePosixPath(target).name)
    (ctx.dev_deps if ctx.dev else ctx.deps).append(name)
    ctx.sources[name] = {"path": target.lstrip("./") or target, "editable": True}
    report.mapped(META.id, line, f"{name} -> path source, editable")
