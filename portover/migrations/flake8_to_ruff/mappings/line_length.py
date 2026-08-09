"""max-line-length / max-doc-length."""

from portover.core import MappingMeta

META = MappingMeta(
    id="line-length",
    directive="max-line-length",
    title="Migrate flake8 max-line-length to ruff",
    before="[flake8]\nmax-line-length = 100",
    after="line-length = 100",
    notes=(
        "Top-level key, shared by ruff's linter AND formatter. If you relied on "
        "flake8's B950-style 10% tolerance, that behaviour maps to E501 exactly, "
        "not loosely."
    ),
    priority=10,
)


def matches(key: str) -> bool:
    return key in ("max-line-length", "max_line_length")


def apply(key: str, value: str, ctx, report) -> None:
    ctx.top["line-length"] = int(value.strip())
    report.mapped(META.id, f"{key} = {value.strip()}")
