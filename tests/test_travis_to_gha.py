from pathlib import Path

from portover.migrations import get
from portover.miniyaml import parse

MIG = get("travis-to-gha")
EXAMPLE = Path(__file__).parent.parent / "examples" / "travis" / ".travis.yml"


def run_file(tmp_path, text):
    (tmp_path / ".travis.yml").write_text(text)
    report = MIG.run(tmp_path)
    return report, report.outputs.get(".github/workflows/ci.yml", "")


# --- miniyaml ---

def test_miniyaml_shapes():
    doc = parse("language: python\npython:\n  - '3.11'\n  - 3.12\nflow: [a, b]\n"
                "nested:\n  key: true\nsame_indent_list:\n- x\n- y\n")
    assert doc["language"] == "python"
    assert doc["python"] == ["3.11", "3.12"]  # 3.12 stays a string, not 3.12 the float
    assert doc["flow"] == ["a", "b"]
    assert doc["nested"] == {"key": True}
    assert doc["same_indent_list"] == ["x", "y"]


def test_miniyaml_list_of_maps():
    doc = parse("jobs:\n  include:\n    - python: '3.13'\n      env: A=1\n    - python: '3.12'\n")
    assert doc["jobs"]["include"] == [{"python": "3.13", "env": "A=1"}, {"python": "3.12"}]


def test_miniyaml_comments():
    doc = parse("# top\nkey: value  # trailing\nurl: 'http://x#y'\n")
    assert doc == {"key": "value", "url": "http://x#y"}


def test_anchor_flagged_not_crashed(tmp_path):
    report, yml = run_file(tmp_path, "base: &b\n  a: 1\n")
    assert yml == ""
    assert any(h.mapping_id == "parse" for h in report.hits)


# --- migration ---

def test_version_matrix_and_setup(tmp_path):
    _, yml = run_file(tmp_path, "language: python\npython: ['3.11', '3.12']\nscript: pytest\n")
    assert "actions/setup-python@v5" in yml
    assert "python-version: ${{ matrix.python }}" in yml
    assert '"3.11"' in yml and '"3.12"' in yml


def test_single_version_no_matrix(tmp_path):
    _, yml = run_file(tmp_path, "language: python\npython: '3.12'\nscript: pytest\n")
    assert "matrix" not in yml
    assert 'python-version: "3.12"' in yml


def test_phase_order_and_conditions(tmp_path):
    _, yml = run_file(tmp_path, "script: pytest\ninstall: pip install .\nafter_failure: cat log\nafter_script: cleanup\n")
    assert yml.index("pip install .") < yml.index("pytest")
    assert "if: failure()" in yml and "if: always()" in yml


def test_services(tmp_path):
    _, yml = run_file(tmp_path, "services:\n  - postgresql\n  - docker\nscript: make test\n")
    assert "image: postgres:16" in yml
    assert "docker" not in yml.split("services:")[1].split("steps:")[0]


def test_env_matrix_rows(tmp_path):
    _, yml = run_file(tmp_path, "env:\n  - DB=postgres\n  - DB=sqlite\nscript: make test\n")
    assert "DB=postgres" in yml and "DB=sqlite" in yml
    assert "$GITHUB_ENV" in yml


def test_branches_regex_to_glob(tmp_path):
    _, yml = run_file(tmp_path, "branches:\n  only:\n    - main\n    - /^release-.*$/\nscript: make\n")
    assert "release-*" in yml and "main" in yml


def test_full_example_kitchen_sink(tmp_path):
    report, yml = run_file(tmp_path, EXAMPLE.read_text())
    for expected in ("runs-on: ubuntu-22.04", "matrix", "cache: pip", "image: postgres:16",
                     "image: redis:7", "REGISTRY: ghcr.io/acme", "fetch-depth: 0",
                     "apt-get install -y libpq-dev", "run: pytest -q", "if: failure()",
                     'python: "3.13"'):
        assert expected in yml, f"missing {expected!r}\n{yml}"
    manual_ids = {h.mapping_id for h in report.hits if h.manual}
    assert {"env", "deploy", "matrix-jobs"} <= manual_ids  # secure, pypi deploy, allow_failures
    assert not report.unmapped


def test_no_script_flagged(tmp_path):
    report, _ = run_file(tmp_path, "language: python\npython: '3.12'\n")
    assert any(h.mapping_id == "script" and h.manual for h in report.hits)
