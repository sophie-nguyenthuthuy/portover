"""--index-url / --extra-index-url."""

from portover.core import MappingMeta

META = MappingMeta(
    id="index-url",
    directive="--index-url / --extra-index-url",
    title="Migrate pip --index-url and --extra-index-url to uv",
    before="--index-url https://pypi.corp.example/simple\n--extra-index-url https://pypi.org/simple",
    after="""[[tool.uv.index]]
name = "corp"
url = "https://pypi.corp.example/simple"
default = true

[[tool.uv.index]]
name = "pypi"
url = "https://pypi.org/simple\"""",
    notes=(
        "uv indexes are named and ordered; `default = true` replaces --index-url. "
        "Unlike pip, uv does not blend indexes per package by default "
        "(no dependency-confusion surprise) — pin a package to an index with "
        "[tool.uv.sources] pkg = { index = \"corp\" } if you need that."
    ),
    priority=10,
)


def matches(line: str) -> bool:
    return line.startswith(("--index-url", "-i ", "--extra-index-url"))


def apply(line: str, ctx, report) -> None:
    parts = line.replace("=", " ", 1).split()
    url = parts[-1]
    default = parts[0] in ("--index-url", "-i")
    host = url.split("//")[-1].split("/")[0].split(".")[0] or "index"
    name = host if all(i["name"] != host for i in ctx.indexes) else f"{host}{len(ctx.indexes)}"
    entry = {"name": name, "url": url}
    if default:
        entry["default"] = True
    ctx.indexes.append(entry)
    report.mapped(META.id, line, f'[[tool.uv.index]] "{name}"' + (" (default)" if default else ""))
