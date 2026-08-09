"""exclude / extend-exclude."""

from portover.core import MappingMeta
from portover.migrations.flake8_to_ruff import split_codes

META = MappingMeta(
    id="exclude",
    directive="exclude / extend-exclude",
    title="Migrate flake8 exclude to ruff",
    before="[flake8]\nexclude = .git,__pycache__,build,migrations",
    after='extend-exclude = ["build", "migrations"]',
    notes=(
        "ruff already excludes .git, __pycache__, virtualenvs and friends by "
        "default, so portover keeps only your non-default entries and uses "
        "extend-exclude to preserve the defaults."
    ),
    priority=12,
)

_DEFAULTS = {".git", "__pycache__", ".tox", ".nox", ".venv", "venv", ".eggs", "*.egg", "*.egg-info",
             ".mypy_cache", ".ruff_cache", ".pytest_cache", "build", "dist", ".svn", ".hg", ".bzr", "node_modules"}


def matches(key: str) -> bool:
    return key.replace("_", "-") in ("exclude", "extend-exclude")


def apply(key: str, value: str, ctx, report) -> None:
    entries = split_codes(value)
    kept = [e for e in entries if e not in _DEFAULTS]
    ctx.top.setdefault("extend-exclude", []).extend(kept)
    skipped = len(entries) - len(kept)
    report.mapped(META.id, f"{key} = {value.strip()}",
                  f"extend-exclude {kept}" + (f"; {skipped} entries already ruff defaults" if skipped else ""))
