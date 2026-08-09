import tomllib
from pathlib import Path

from portover.migrations import get

MIG = get("flake8-to-ruff")
EXAMPLE = Path(__file__).parent.parent / "examples" / "flake8" / ".flake8"


def run_cfg(tmp_path, text, fname=".flake8"):
    (tmp_path / fname).write_text(text)
    report = MIG.run(tmp_path)
    return report, tomllib.loads(report.outputs["ruff.toml"])


def test_full_example(tmp_path):
    report, doc = run_cfg(tmp_path, EXAMPLE.read_text())
    assert doc["line-length"] == 100
    assert doc["lint"]["extend-ignore"] == ["E203"]  # W503 dropped
    assert "migrations" in doc["extend-exclude"] and "build" not in doc["extend-exclude"]
    assert doc["lint"]["per-file-ignores"]["tests/*"] == ["S101", "D103"]
    assert doc["lint"]["mccabe"]["max-complexity"] == 10
    assert "C901" in doc["lint"]["extend-select"]
    assert not report.unmapped


def test_w503_drop_is_reported(tmp_path):
    report, _ = run_cfg(tmp_path, "[flake8]\nignore = W503, E501\n")
    hit = next(h for h in report.hits if h.mapping_id == "select-ignore")
    assert "W503" in hit.detail


def test_setup_cfg_section(tmp_path):
    _, doc = run_cfg(tmp_path, "[metadata]\nname = x\n\n[flake8]\nmax-line-length = 88\n", fname="setup.cfg")
    assert doc["line-length"] == 88


def test_unknown_key_unmapped(tmp_path):
    report, _ = run_cfg(tmp_path, "[flake8]\nsome-plugin-option = 3\n")
    assert any("some-plugin-option" in u for u in report.unmapped)
