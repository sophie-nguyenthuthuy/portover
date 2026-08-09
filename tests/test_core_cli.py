import tomllib
from pathlib import Path

from portover import __version__
from portover.cli import main
from portover.core import MappingMeta, load_mappings
from portover.docsgen import generate
from portover.migrations import REGISTRY


def test_package_versions_match():
    pyproject = Path(__file__).parent.parent / "pyproject.toml"
    project_version = tomllib.loads(pyproject.read_text())["project"]["version"]
    assert __version__ == project_version


def test_every_mapping_has_complete_meta():
    for migration in REGISTRY:
        mods = migration.mappings()
        assert mods, migration.id
        ids = [m.META.id for m in mods]
        assert len(ids) == len(set(ids)), f"duplicate mapping ids in {migration.id}"
        for mod in mods:
            meta = mod.META
            assert isinstance(meta, MappingMeta)
            assert meta.title and meta.before and meta.after, f"{migration.id}/{meta.id} missing docs fields"
            assert callable(mod.matches)


def test_load_mappings_sorted_by_priority():
    mods = load_mappings("portover.migrations.pip_to_uv")
    prios = [m.META.priority for m in mods]
    assert prios == sorted(prios)
    assert mods[-1].META.id == "requirement"  # generic fallback last


def test_cli_list_and_detect(tmp_path, capsys):
    assert main(["list"]) == 0
    assert "pip-to-uv" in capsys.readouterr().out
    (tmp_path / "requirements.txt").write_text("requests\n")
    assert main(["detect", str(tmp_path)]) == 0
    assert "pip-to-uv" in capsys.readouterr().out


def test_cli_run_write(tmp_path, capsys):
    (tmp_path / "requirements.txt").write_text("requests>=2.31\n")
    assert main(["run", "pip-to-uv", str(tmp_path), "--write"]) == 0
    doc = tomllib.loads((tmp_path / "pyproject.toml").read_text())
    assert doc["project"]["dependencies"] == ["requests>=2.31"]
    assert "Manual steps" in capsys.readouterr().out  # uv lock reminder


def test_cli_unknown_migration(capsys):
    assert main(["run", "nope-to-nothing", "."]) == 2


def test_docsgen_writes_page_per_mapping(tmp_path):
    n = generate(tmp_path)
    total_mappings = sum(len(m.mappings()) for m in REGISTRY)
    assert n == total_mappings + len(REGISTRY) + 1
    page = (tmp_path / "pip-to-uv" / "editable.md").read_text()
    assert "editable" in page and "Before" in page and "After" in page
