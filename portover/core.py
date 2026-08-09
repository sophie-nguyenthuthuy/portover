"""Core engine: migrations are folders of mappings; a mapping handles one directive.

The contract:

- A *migration* converts one config dialect to another (pip -> uv).
- A *mapping* is a single file in the migration's ``mappings/`` package that
  handles exactly one source directive (``-e``, ``post { always }``,
  ``max-line-length``). It declares ``META`` (used for docs + reports) and the
  hooks the migration's driver calls.
- Anything no mapping claims is surfaced as a manual step, never silently
  dropped.
"""

from __future__ import annotations

import importlib
import pkgutil
from dataclasses import dataclass, field


@dataclass(frozen=True)
class MappingMeta:
    """Docs-facing description of one directive mapping.

    ``before``/``after`` are real snippets: they become the generated doc page
    and the report examples, so keep them copy-pasteable.
    """

    id: str
    directive: str
    title: str
    before: str
    after: str
    notes: str = ""
    manual: bool = False  # True when the mapping can only flag, not convert
    priority: int = 50  # lower runs first; specific mappings go before generic


@dataclass
class Hit:
    mapping_id: str
    source: str
    detail: str = ""
    manual: bool = False


@dataclass
class Report:
    migration_id: str
    hits: list[Hit] = field(default_factory=list)
    unmapped: list[str] = field(default_factory=list)
    outputs: dict[str, str] = field(default_factory=dict)  # relative path -> content

    def mapped(self, mapping_id: str, source: str, detail: str = "") -> None:
        self.hits.append(Hit(mapping_id, source, detail))

    def manual(self, mapping_id: str, source: str, detail: str) -> None:
        self.hits.append(Hit(mapping_id, source, detail, manual=True))

    def counts(self) -> dict[str, tuple[int, bool]]:
        out: dict[str, tuple[int, bool]] = {}
        for h in self.hits:
            n, man = out.get(h.mapping_id, (0, False))
            out[h.mapping_id] = (n + 1, man or h.manual)
        return out


def load_mappings(package: str) -> list:
    """Import every module in ``<package>.mappings`` and return them sorted by
    META.priority. Dropping a new file into mappings/ is the whole
    registration step."""
    pkg = importlib.import_module(package + ".mappings")
    mods = []
    for info in pkgutil.iter_modules(pkg.__path__):
        mod = importlib.import_module(f"{package}.mappings.{info.name}")
        if hasattr(mod, "META"):
            mods.append(mod)
    return sorted(mods, key=lambda m: (m.META.priority, m.META.id))


class Migration:
    """Subclass contract: set id/source/target/package, implement detect() and run()."""

    id: str = ""
    source: str = ""
    target: str = ""
    package: str = ""  # dotted path holding the mappings/ package

    def mappings(self) -> list:
        return load_mappings(self.package)

    def detect(self, root) -> list[str]:
        """Return relative paths of files this migration would consume."""
        raise NotImplementedError

    def run(self, root) -> Report:
        raise NotImplementedError
