"""--find-links / -f."""

from portover.core import MappingMeta

META = MappingMeta(
    id="find-links",
    directive="--find-links / -f",
    title="Migrate pip --find-links to uv",
    before="--find-links https://download.pytorch.org/whl/cpu",
    after="""[[tool.uv.index]]
name = "pytorch"
url = "https://download.pytorch.org/whl/cpu"
format = "flat\"""",
    notes="A flat (find-links style) listing becomes a uv index with format = \"flat\".",
    priority=12,
)


def matches(line: str) -> bool:
    return line.startswith(("--find-links", "-f "))


def apply(line: str, ctx, report) -> None:
    url = line.replace("=", " ", 1).split()[-1]
    name = f"flat{len(ctx.indexes) or ''}"
    ctx.indexes.append({"name": name, "url": url, "format": "flat"})
    report.mapped(META.id, line, f'flat index "{name}"')
