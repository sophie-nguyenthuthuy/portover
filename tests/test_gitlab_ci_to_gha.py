from pathlib import Path

import yaml

from portover.migrations import get
from portover.migrations.gitlab_ci_to_gha.expr import translate

MIG = get("gitlab-ci-to-gha")
EXAMPLE = Path(__file__).parent.parent / "examples" / "gitlab" / ".gitlab-ci.yml"


def run_file(tmp_path, text):
    (tmp_path / ".gitlab-ci.yml").write_text(text)
    report = MIG.run(tmp_path)
    return report, report.outputs.get(".github/workflows/ci.yml", "")


def jobs_of(yml):
    doc = yaml.safe_load(yml)
    return doc["jobs"]


# --- rule expression translation ---

def test_translate_common_conditions():
    assert translate('$CI_COMMIT_BRANCH == "main"') == "github.ref_name == 'main'"
    assert translate('$CI_PIPELINE_SOURCE == "merge_request_event"') == "github.event_name == 'pull_request'"
    assert translate("$CI_COMMIT_TAG") == "github.ref_type == 'tag'"
    assert translate("$CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH") == (
        "github.ref_name == github.event.repository.default_branch")
    assert translate('$MY_FLAG == "yes"') == "env.MY_FLAG == 'yes'"


def test_translate_logical_and_regex():
    assert translate('$CI_COMMIT_BRANCH == "main" && $CI_PIPELINE_SOURCE == "push"') == (
        "github.ref_name == 'main' && github.event_name == 'push'")
    assert translate('$CI_COMMIT_TAG =~ /^v/') == "startsWith(github.ref_name, 'v')"


def test_translate_gives_up_loudly():
    assert translate("$CI_COMMIT_MESSAGE =~ /(?i)wip/") is None


# --- structure ---

def test_stages_become_needs_chain(tmp_path):
    _, yml = run_file(tmp_path,
                      "stages: [build, test]\n"
                      "a:\n  stage: build\n  script: make a\n"
                      "b:\n  stage: test\n  script: make b\n"
                      "c:\n  stage: test\n  script: make c\n")
    jobs = jobs_of(yml)
    assert "needs" not in jobs["a"]
    assert jobs["b"]["needs"] == "a" and jobs["c"]["needs"] == "a"


def test_explicit_needs_overrides_stage_order(tmp_path):
    _, yml = run_file(tmp_path,
                      "stages: [build, test]\n"
                      "a:\n  stage: build\n  script: make a\n"
                      "b:\n  stage: test\n  needs: []\n  script: make b\n")
    assert "needs" not in jobs_of(yml)["b"]


def test_extends_merges_template(tmp_path):
    _, yml = run_file(tmp_path,
                      ".base:\n  image: python:3.12\n  before_script:\n    - pip install .\n"
                      "test:\n  extends: .base\n  script: pytest\n")
    jobs = jobs_of(yml)
    assert ".base" not in jobs and "base" not in jobs  # templates are never emitted
    assert jobs["test"]["container"] == "python:3.12"
    runs = [s["run"] for s in jobs["test"]["steps"] if "run" in s]
    assert runs == ["pip install .", "pytest"]


def test_hidden_template_not_emitted_as_job(tmp_path):
    report, yml = run_file(tmp_path, ".hidden:\n  script: nope\nreal:\n  script: yes\n")
    assert list(jobs_of(yml)) == ["real"]


def test_job_name_slugged_and_preserved(tmp_path):
    _, yml = run_file(tmp_path, "unit tests:\n  script: pytest\n")
    job = jobs_of(yml)["unit-tests"]
    assert job["name"] == "unit tests"


def test_ci_variables_defined_only_when_used(tmp_path):
    _, yml = run_file(tmp_path, "a:\n  script:\n    - echo $CI_COMMIT_SHA\n")
    env = yaml.safe_load(yml)["env"]
    assert env["CI_COMMIT_SHA"] == "${{ github.sha }}"
    assert "CI_PIPELINE_ID" not in env  # unused ones are not invented


def test_short_sha_flagged_not_faked(tmp_path):
    report, _ = run_file(tmp_path, "a:\n  script:\n    - echo $CI_COMMIT_SHORT_SHA\n")
    assert any(h.mapping_id == "ci-variables" and h.manual and "SHORT_SHA" in h.source
               for h in report.hits)


def test_parallel_count_sets_node_index(tmp_path):
    _, yml = run_file(tmp_path, "a:\n  parallel: 3\n  script: pytest\n")
    job = jobs_of(yml)["a"]
    assert job["strategy"]["matrix"]["CI_NODE_INDEX"] == [1, 2, 3]
    assert job["env"]["CI_NODE_TOTAL"] == 3


def test_only_except_conditions(tmp_path):
    _, yml = run_file(tmp_path, "a:\n  only:\n    - main\n  except:\n    - schedules\n  script: make\n")
    condition = jobs_of(yml)["a"]["if"]
    assert "github.ref_name == 'main'" in condition
    assert "!(github.event_name == 'schedule')" in condition


def test_allow_failure_and_timeout(tmp_path):
    _, yml = run_file(tmp_path, "a:\n  allow_failure: true\n  timeout: 1h 30m\n  script: make\n")
    job = jobs_of(yml)["a"]
    assert job["continue-on-error"] is True
    assert job["timeout-minutes"] == 90


def test_static_cache_key_is_flagged(tmp_path):
    report, _ = run_file(tmp_path, "a:\n  cache:\n    key: build-cache\n    paths: [.cache]\n  script: make\n")
    assert any(h.mapping_id == "cache" and h.manual and "immutable" in h.detail for h in report.hits)


def test_manual_job_gets_environment_gate(tmp_path):
    report, yml = run_file(tmp_path, "deploy:\n  when: manual\n  script: ./deploy.sh\n")
    assert jobs_of(yml)["deploy"]["environment"] == "manual-approval"
    assert any(h.mapping_id == "when" and h.manual for h in report.hits)


def test_full_example_kitchen_sink(tmp_path):
    report, yml = run_file(tmp_path, EXAMPLE.read_text())
    doc = yaml.safe_load(yml)
    jobs = doc["jobs"]
    assert list(jobs) == ["compile", "unit-tests", "lint", "deploy"]
    assert jobs["deploy"]["needs"] == ["unit-tests", "lint"]
    assert jobs["deploy"]["if"] == "github.ref_name == 'main'"
    assert jobs["unit-tests"]["strategy"]["matrix"]["PYTHON"] == ["3.11", "3.12"]
    assert jobs["unit-tests"]["services"]["cache"]["image"] == "redis:7"  # alias wins
    assert jobs["lint"]["continue-on-error"] is True
    assert doc["concurrency"]["cancel-in-progress"] is True  # interruptible
    assert jobs["deploy"]["concurrency"]["cancel-in-progress"] is False  # resource_group
    assert not report.unmapped


def test_job_key_order_and_valid_structure(tmp_path):
    _, yml = run_file(tmp_path, EXAMPLE.read_text())
    deploy = yml.split("  deploy:\n")[1]
    assert deploy.index("needs:") < deploy.index("runs-on:") < deploy.index("steps:")
    assert deploy.index("concurrency:") < deploy.index("steps:")
    for job in jobs_of(yml).values():
        assert all(("run" in s) or ("uses" in s) for s in job["steps"])


def test_anchor_is_reported(tmp_path):
    report, yml = run_file(tmp_path, "base: &base\n  script: make\n")
    assert not yml
    assert any(h.mapping_id == "parse" and h.manual for h in report.hits)
