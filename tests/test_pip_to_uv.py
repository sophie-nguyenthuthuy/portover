import tomllib

from portover.migrations import get

MIG = get("pip-to-uv")


def run_lines(tmp_path, text, fname="requirements.txt"):
    (tmp_path / fname).write_text(text)
    report = MIG.run(tmp_path)
    out = next(iter(report.outputs.values()))
    return report, tomllib.loads(out)


def test_plain_requirements(tmp_path):
    _, doc = run_lines(tmp_path, 'requests>=2.31\ncelery[redis]==5.4.0\ntomli; python_version < "3.11"\n')
    deps = doc["project"]["dependencies"]
    assert "requests>=2.31" in deps
    assert "celery[redis]==5.4.0" in deps
    assert any(d.startswith("tomli;") or d.startswith("tomli ;") for d in deps)


def test_editable_local(tmp_path):
    _, doc = run_lines(tmp_path, "-e ./libs/toolkit\n")
    assert "toolkit" in doc["project"]["dependencies"]
    assert doc["tool"]["uv"]["sources"]["toolkit"] == {"path": "libs/toolkit", "editable": True}


def test_editable_dot_dropped(tmp_path):
    report, doc = run_lines(tmp_path, "-e .\n")
    assert doc["project"]["dependencies"] == []
    assert any(h.mapping_id == "editable" and not h.manual for h in report.hits)


def test_vcs_with_rev_and_egg(tmp_path):
    _, doc = run_lines(tmp_path, "git+https://github.com/psf/requests.git@v2.32.3#egg=reqgit\n")
    src = doc["tool"]["uv"]["sources"]["reqgit"]
    assert src == {"git": "https://github.com/psf/requests.git", "rev": "v2.32.3"}


def test_index_urls(tmp_path):
    _, doc = run_lines(tmp_path, "--index-url https://pypi.corp.example/simple\n--extra-index-url https://pypi.org/simple\nrequests\n")
    idx = doc["tool"]["uv"]["index"]
    assert idx[0]["default"] is True
    assert idx[0]["url"] == "https://pypi.corp.example/simple"
    assert "default" not in idx[1]


def test_hashes_stripped_and_flagged(tmp_path):
    report, doc = run_lines(tmp_path, "requests==2.32.3 --hash=sha256:aaaa --hash=sha256:bbbb\n")
    assert doc["project"]["dependencies"] == ["requests==2.32.3"]
    assert any(h.mapping_id == "hashes" for h in report.hits)


def test_include_flagged_manual(tmp_path):
    report, _ = run_lines(tmp_path, "-r base.txt\n-c constraints.txt\n")
    manual = [h for h in report.hits if h.mapping_id == "include"]
    assert len(manual) == 2 and all(h.manual for h in manual)


def test_option_flags(tmp_path):
    _, doc = run_lines(tmp_path, "--pre\n--no-binary grpcio\n--only-binary :all:\n")
    uv = doc["tool"]["uv"]
    assert uv["prerelease"] == "allow"
    assert uv["no-binary-package"] == ["grpcio"]
    assert uv["no-build"] is True


def test_dev_requirements_go_to_group(tmp_path):
    (tmp_path / "requirements.txt").write_text("requests\n")
    (tmp_path / "requirements-dev.txt").write_text("pytest>=8\n")
    report = MIG.run(tmp_path)
    doc = tomllib.loads(next(iter(report.outputs.values())))
    assert doc["project"]["dependencies"] == ["requests"]
    assert doc["dependency-groups"]["dev"] == ["pytest>=8"]


def test_existing_pyproject_not_clobbered(tmp_path):
    (tmp_path / "requirements.txt").write_text("requests\n")
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "x"\n')
    report = MIG.run(tmp_path)
    assert "pyproject.portover.toml" in report.outputs
    assert any(h.mapping_id == "merge" for h in report.hits)


def test_continuation_and_comments(tmp_path):
    _, doc = run_lines(tmp_path, "# comment\nrequests \\\n    >=2.31  # trailing\n\n")
    assert doc["project"]["dependencies"] == ["requests >=2.31"]


def test_unmapped_surfaces(tmp_path):
    report, _ = run_lines(tmp_path, "--some-unknown-flag foo\n")
    assert report.unmapped
