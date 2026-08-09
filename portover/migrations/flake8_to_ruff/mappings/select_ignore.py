"""select / ignore / extend-select / extend-ignore."""

from portover.core import MappingMeta
from portover.migrations.flake8_to_ruff import split_codes

META = MappingMeta(
    id="select-ignore",
    directive="select / ignore / extend-select / extend-ignore",
    title="Migrate flake8 select and ignore lists to ruff",
    before="[flake8]\nextend-ignore = E203, W503",
    after='[lint]\nextend-ignore = ["E203"]  # W503 does not exist in ruff',
    notes=(
        "pycodestyle/pyflakes codes (E/W/F) carry over 1:1. W503/W504 don't "
        "exist in ruff (its formatter settles the operator-break argument). "
        "Plugin codes move to ruff's re-implementations: B* needs "
        "flake8-bugbear -> select B, C4* -> C4, S* (bandit) -> S — enable those "
        "prefixes in [lint] select."
    ),
    priority=10,
)

_KEYS = {"select": "select", "extend-select": "extend-select",
         "ignore": "ignore", "extend-ignore": "extend-ignore"}
_GONE = {"W503", "W504"}


def matches(key: str) -> bool:
    return key.replace("_", "-") in _KEYS


def apply(key: str, value: str, ctx, report) -> None:
    ruff_key = _KEYS[key.replace("_", "-")]
    codes = split_codes(value)
    kept = [c for c in codes if c not in _GONE]
    ctx.lint[ruff_key] = kept
    dropped = sorted(set(codes) - set(kept))
    if dropped:
        report.mapped(META.id, f"{key} = {value.strip()}",
                      f"{ruff_key}; dropped {', '.join(dropped)} (not implemented by ruff — formatter territory)")
    else:
        report.mapped(META.id, f"{key} = {value.strip()}", f"[lint] {ruff_key}")
