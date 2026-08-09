"""max-complexity (mccabe)."""

from portover.core import MappingMeta

META = MappingMeta(
    id="mccabe",
    directive="max-complexity",
    title="Migrate flake8 max-complexity to ruff",
    before="[flake8]\nmax-complexity = 10",
    after='[lint]\nextend-select = ["C901"]\n\n[lint.mccabe]\nmax-complexity = 10',
    notes=(
        "Setting the threshold is not enough in ruff — the C901 rule must also "
        "be selected, so portover adds it to extend-select."
    ),
    priority=14,
)


def matches(key: str) -> bool:
    return key.replace("_", "-") == "max-complexity"


def apply(key: str, value: str, ctx, report) -> None:
    ctx.mccabe["max-complexity"] = int(value.strip())
    sel = ctx.lint.setdefault("extend-select", [])
    if "C901" not in sel:
        sel.append("C901")
    report.mapped(META.id, f"{key} = {value.strip()}", "C901 selected + [lint.mccabe] threshold")
