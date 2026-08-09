"""Local paths and archives (./pkg, ../lib, dist/x.whl)."""

from pathlib import PurePosixPath

from portover.core import MappingMeta
from portover.migrations.pip_to_uv import req_name

META = MappingMeta(
    id="local-path",
    directive="./local/pkg or wheel/sdist path",
    title="Migrate pip local path requirements to uv",
    before="./vendor/toolkit\ndist/proto-1.2.0-py3-none-any.whl",
    after="""dependencies = ["toolkit", "proto"]

[tool.uv.sources]
toolkit = { path = "vendor/toolkit" }
proto = { path = "dist/proto-1.2.0-py3-none-any.whl" }""",
    notes="Like every non-registry dep in uv: name in [project], location in [tool.uv.sources].",
    priority=35,
)

_ARCHIVES = (".whl", ".tar.gz", ".zip", ".tar.bz2")


def matches(line: str) -> bool:
    return (line.startswith(("./", "../", "/")) or line.endswith(_ARCHIVES)) and "://" not in line


def apply(line: str, ctx, report) -> None:
    leaf = PurePosixPath(line).name
    for suf in _ARCHIVES:
        leaf = leaf.removesuffix(suf)
    name = req_name(leaf.split("-")[0])
    (ctx.dev_deps if ctx.dev else ctx.deps).append(name)
    ctx.sources[name] = {"path": line.lstrip("./") if line.startswith("./") else line}
    report.mapped(META.id, line, f"{name} -> path source")
