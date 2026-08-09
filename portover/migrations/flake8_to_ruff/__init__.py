""".flake8 / setup.cfg [flake8] -> ruff.toml.

Driver: read the [flake8] section wherever it lives, hand each option key to
the mapping that claims it, render ruff.toml from RuffContext.
"""

from __future__ import annotations

import configparser
from dataclasses import dataclass, field
from pathlib import Path

from portover.core import Migration, Report
from portover.emit import toml_str, toml_value


def split_codes(value: str) -> list[str]:
    return [c.strip() for c in value.replace("\n", ",").split(",") if c.strip()]


@dataclass
class RuffContext:
    top: dict = field(default_factory=dict)  # top-level ruff.toml keys
    lint: dict = field(default_factory=dict)  # [lint]
    per_file: dict = field(default_factory=dict)  # [lint.per-file-ignores]
    mccabe: dict = field(default_factory=dict)  # [lint.mccabe]


class Flake8ToRuff(Migration):
    id = "flake8-to-ruff"
    source = ".flake8 / setup.cfg [flake8]"
    target = "ruff.toml"
    package = "portover.migrations.flake8_to_ruff"

    def detect(self, root) -> list[str]:
        root = Path(root)
        found = []
        for fname in (".flake8", "setup.cfg", "tox.ini"):
            p = root / fname
            if p.exists():
                cp = configparser.ConfigParser()
                try:
                    cp.read(p)
                except configparser.Error:
                    continue
                if cp.has_section("flake8"):
                    found.append(fname)
        return found

    def run(self, root) -> Report:
        root = Path(root)
        report = Report(self.id)
        ctx = RuffContext()
        mappings = self.mappings()
        for fname in self.detect(root):
            cp = configparser.ConfigParser()
            cp.read(root / fname)
            for key, value in cp.items("flake8"):
                for m in mappings:
                    if m.matches(key):
                        m.apply(key, value, ctx, report)
                        break
                else:
                    report.unmapped.append(f"{fname}: {key} = {value.strip()}")
        report.outputs["ruff.toml"] = self._render(ctx)
        report.manual("verify", "ruff.toml",
                      "run `ruff check .` and compare with flake8's output; rule code semantics differ slightly")
        return report

    def _render(self, ctx: RuffContext) -> str:
        parts = [f"{k} = {toml_value(v)}" for k, v in ctx.top.items()]
        if ctx.lint:
            parts += ["", "[lint]"] + [f"{k} = {toml_value(v)}" for k, v in ctx.lint.items()]
        if ctx.mccabe:
            parts += ["", "[lint.mccabe]"] + [f"{k} = {toml_value(v)}" for k, v in ctx.mccabe.items()]
        if ctx.per_file:
            parts += ["", "[lint.per-file-ignores]"]
            parts += [f"{toml_str(pat)} = {toml_value(codes)}" for pat, codes in ctx.per_file.items()]
        return "\n".join(parts).lstrip("\n") + "\n"


MIGRATION = Flake8ToRuff()
