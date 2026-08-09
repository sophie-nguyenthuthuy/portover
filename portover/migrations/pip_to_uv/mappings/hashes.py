"""--hash pinned lines (pip-compile output)."""

import re

from portover.core import MappingMeta
from portover.migrations.pip_to_uv import req_name

META = MappingMeta(
    id="hashes",
    directive="pkg==1.2 --hash=sha256:...",
    title="Migrate pip --hash pinned requirements to uv",
    before="requests==2.32.3 --hash=sha256:5559... --hash=sha256:9a38...",
    after="""dependencies = ["requests==2.32.3"]
# hashes live in uv.lock — generated, verified on install, never hand-edited""",
    notes=(
        "Hash-pinned files are usually pip-compile output. Point portover at the "
        "*source* requirements.in if you have one; either way uv.lock takes over "
        "hash pinning the moment you run `uv lock`."
    ),
    priority=20,
)


def matches(line: str) -> bool:
    return "--hash=" in line


def apply(line: str, ctx, report) -> None:
    spec = re.sub(r"\s+--hash=\S+", "", line).strip().rstrip("\\").strip()
    (ctx.dev_deps if ctx.dev else ctx.deps).append(spec)
    report.mapped(META.id, line, f"{req_name(spec)}: hashes dropped — uv.lock re-pins them")
