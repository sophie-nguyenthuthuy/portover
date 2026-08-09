"""requirements.txt -> uv (pyproject.toml).

Driver: normalize lines (comments, continuations), give every line to the
first mapping that claims it, then render a pyproject.toml from what the
mappings collected into PipContext.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from portover.core import Migration, Report
from portover.emit import toml_value

REQ_FILES = ("requirements.txt", "requirements-dev.txt", "requirements_dev.txt", "dev-requirements.txt")

_NAME_RE = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._-]*)")


def req_name(spec: str) -> str:
    """Best-effort distribution name from a PEP 508 spec."""
    m = _NAME_RE.match(spec.strip())
    return (m.group(1) if m else spec).lower().replace("_", "-").replace(".", "-")


@dataclass
class PipContext:
    deps: list[str] = field(default_factory=list)  # [project] dependencies
    dev_deps: list[str] = field(default_factory=list)  # [dependency-groups] dev
    sources: dict[str, dict] = field(default_factory=dict)  # [tool.uv.sources]
    indexes: list[dict] = field(default_factory=list)  # [[tool.uv.index]]
    settings: dict = field(default_factory=dict)  # [tool.uv] flat keys
    dev: bool = False  # True while processing a dev requirements file


def normalize_lines(text: str):
    """Strip comments, join backslash continuations, drop blanks."""
    joined: list[str] = []
    pending = ""
    for raw in text.splitlines():
        line = re.sub(r"(^|\s)#.*$", "", raw).strip()
        if not line:
            continue
        if line.endswith("\\"):
            pending += line[:-1] + " "
            continue
        joined.append(" ".join((pending + line).split()))
        pending = ""
    if pending.strip():
        joined.append(pending.strip())
    return joined


class PipToUv(Migration):
    id = "pip-to-uv"
    source = "requirements.txt (pip)"
    target = "pyproject.toml (uv)"
    package = "portover.migrations.pip_to_uv"

    def detect(self, root) -> list[str]:
        root = Path(root)
        return [f for f in REQ_FILES if (root / f).exists()]

    def run(self, root) -> Report:
        root = Path(root)
        report = Report(self.id)
        ctx = PipContext()
        mappings = self.mappings()
        for fname in self.detect(root):
            ctx.dev = "dev" in fname
            for line in normalize_lines((root / fname).read_text()):
                for m in mappings:
                    if m.matches(line):
                        m.apply(line, ctx, report)
                        break
                else:
                    report.unmapped.append(f"{fname}: {line}")
        report.outputs[self._out_name(root)] = self._render(root, ctx)
        if (root / "pyproject.toml").exists():
            report.manual("merge", "pyproject.toml",
                          "pyproject.toml already exists — merge pyproject.portover.toml into it by hand")
        report.manual("lock", "uv.lock", "run `uv lock` (then `uv sync`) to produce the lockfile")
        return report

    def _out_name(self, root: Path) -> str:
        return "pyproject.portover.toml" if (root / "pyproject.toml").exists() else "pyproject.toml"

    def _render(self, root: Path, ctx: PipContext) -> str:
        name = re.sub(r"[^a-z0-9-]+", "-", root.resolve().name.lower()).strip("-") or "migrated-project"
        parts = [
            "[project]",
            f'name = "{name}"',
            'version = "0.1.0"',
            'requires-python = ">=3.9"',
            f"dependencies = {toml_value(sorted(ctx.deps))}",
        ]
        if ctx.dev_deps:
            parts += ["", "[dependency-groups]", f"dev = {toml_value(sorted(ctx.dev_deps))}"]
        for idx in ctx.indexes:
            parts += ["", "[[tool.uv.index]]"] + [f"{k} = {toml_value(v)}" for k, v in idx.items()]
        if ctx.sources:
            parts += ["", "[tool.uv.sources]"]
            parts += [f"{n} = {toml_value(src)}" for n, src in sorted(ctx.sources.items())]
        if ctx.settings:
            parts += ["", "[tool.uv]"]
            parts += [f"{k} = {toml_value(v)}" for k, v in sorted(ctx.settings.items())]
        return "\n".join(parts) + "\n"


MIGRATION = PipToUv()
