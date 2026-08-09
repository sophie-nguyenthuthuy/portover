"""Plain PEP 508 requirement lines — the generic fallback (highest priority number)."""

import re

from portover.core import MappingMeta

META = MappingMeta(
    id="requirement",
    directive='pkg==1.2, pkg[extra]>=2, pkg; python_version<"3.11"',
    title="Migrate plain requirements.txt lines to uv",
    before='requests>=2.31\ncelery[redis]==5.4.0\ntomli; python_version < "3.11"',
    after="""[project]
dependencies = [
    "requests>=2.31",
    "celery[redis]==5.4.0",
    'tomli; python_version < "3.11"',
]""",
    notes=(
        "Specifiers, extras and environment markers are already PEP 508 — they "
        "move into [project] dependencies verbatim. Dev requirement files land "
        "in [dependency-groups] dev instead."
    ),
    priority=90,
)

_REQ = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*\s*(\[[^\]]*\])?\s*([<>=!~;@ ].*)?$")


def matches(line: str) -> bool:
    return bool(_REQ.match(line)) and not line.startswith("-")


def apply(line: str, ctx, report) -> None:
    (ctx.dev_deps if ctx.dev else ctx.deps).append(line)
    report.mapped(META.id, line)
