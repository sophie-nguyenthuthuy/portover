"""per-file-ignores."""

from portover.core import MappingMeta
from portover.migrations.flake8_to_ruff import split_codes

META = MappingMeta(
    id="per-file-ignores",
    directive="per-file-ignores",
    title="Migrate flake8 per-file-ignores to ruff",
    before="[flake8]\nper-file-ignores =\n    tests/*: S101,D103\n    __init__.py: F401",
    after='[lint.per-file-ignores]\n"tests/*" = ["S101", "D103"]\n"__init__.py" = ["F401"]',
    notes="Same pattern:codes idea, TOML table instead of ini lines. Patterns are quoted TOML keys.",
    priority=12,
)


def matches(key: str) -> bool:
    return key.replace("_", "-") == "per-file-ignores"


def apply(key: str, value: str, ctx, report) -> None:
    for line in value.strip().splitlines():
        if ":" not in line:
            continue
        pattern, _, codes = line.partition(":")
        ctx.per_file[pattern.strip()] = split_codes(codes)
        report.mapped(META.id, line.strip())
