from pathlib import Path

import yaml

from portover.migrations import get
from portover.migrations.buildkite_to_gha.expr import translate

MIG = get("buildkite-to-gha")
EXAMPLE = Path(__file__).parent.parent / "examples" / "buildkite" / ".buildkite" / "pipeline.yml"


def run_file(tmp_path, text):
    (tmp_path / ".buildkite").mkdir(exist_ok=True)
    (tmp_path / ".buildkite" / "pipeline.yml").write_text(text)
    report = MIG.run(tmp_path)
    return report, report.outputs.get(".github/workflows/ci.yml", "")


def jobs_of(yml):
    return yaml.safe_load(yml)["jobs"]


# --- condition translation ---

def test_translate_common_conditions():
    assert translate('build.branch == "main"') == "github.ref_name == 'main'"
    assert translate("build.tag == null") == "github.ref_type != 'tag'"
    assert translate("build.pull_request.id != null") == "github.event_name == 'pull_request'"
    assert translate('build.env("DEPLOY") == "true"') == "env.DEPLOY == 'true'"


def test_translate_logical_and_regex():
    assert translate('build.branch == "main" && build.tag == null') == (
        "github.ref_name == 'main' && github.ref_type != 'tag'")
    assert translate("build.branch =~ /^release/") == "startsWith(github.ref_name, 'release')"


def test_translate_source_maps_to_event_name():
    assert translate('build.source == "schedule"') == "github.event_name == 'schedule'"


def test_translate_gives_up_loudly():
    assert translate("build.creator.teams includes 'ops'") is None


# --- the wait barrier ---

def test_steps_are_parallel_until_a_wait(tmp_path):
    _, yml = run_file(tmp_path,
                      "steps:\n"
                      "  - label: A\n    command: make a\n"
                      "  - label: B\n    command: make b\n")
    jobs = jobs_of(yml)
    assert "needs" not in jobs["a"] and "needs" not in jobs["b"]


def test_wait_becomes_needs_on_everything_before_it(tmp_path):
    _, yml = run_file(tmp_path,
                      "steps:\n"
                      "  - label: A\n    command: make a\n"
                      "  - label: B\n    command: make b\n"
                      "  - wait\n"
                      "  - label: C\n    command: make c\n")
    jobs = jobs_of(yml)
    assert jobs["c"]["needs"] == ["a", "b"]


def test_second_wait_only_needs_the_latest_group(tmp_path):
    _, yml = run_file(tmp_path,
                      "steps:\n"
                      "  - label: A\n    command: make a\n"
                      "  - wait\n"
                      "  - label: B\n    command: make b\n"
                      "  - wait\n"
                      "  - label: C\n    command: make c\n")
    jobs = jobs_of(yml)
    assert jobs["b"]["needs"] == "a"
    assert jobs["c"]["needs"] == "b"  # transitively covers A


def test_depends_on_key_overrides_barrier(tmp_path):
    _, yml = run_file(tmp_path,
                      "steps:\n"
                      "  - label: A\n    key: alpha\n    command: make a\n"
                      "  - label: B\n    command: make b\n"
                      "  - wait\n"
                      "  - label: C\n    depends_on: alpha\n    command: make c\n")
    # the job id comes from the key, and C waits only on it — not on the whole barrier
    assert jobs_of(yml)["c"]["needs"] == "alpha"


# --- naming ---

def test_emoji_labels_do_not_pollute_job_ids(tmp_path):
    _, yml = run_file(tmp_path, "steps:\n  - label: ':docker: Build image'\n    command: make\n")
    jobs = jobs_of(yml)
    assert list(jobs) == ["build-image"]
    assert jobs["build-image"]["name"] == "Build image"


def test_key_wins_over_label_for_the_job_id(tmp_path):
    _, yml = run_file(tmp_path, "steps:\n  - label: ':test: Run the tests'\n    key: tests\n    command: make\n")
    assert list(jobs_of(yml)) == ["tests"]


# --- step fields ---

def test_parallelism_recreates_buildkite_shard_vars(tmp_path):
    _, yml = run_file(tmp_path,
                      "steps:\n  - label: T\n    parallelism: 3\n"
                      "    command: pytest --shard $BUILDKITE_PARALLEL_JOB\n")
    job = jobs_of(yml)["t"]
    assert job["strategy"]["matrix"]["BUILDKITE_PARALLEL_JOB"] == [0, 1, 2]  # 0-based like Buildkite
    assert job["env"]["BUILDKITE_PARALLEL_JOB_COUNT"] == 3


def test_matrix_interpolation_rewritten(tmp_path):
    _, yml = run_file(tmp_path,
                      "steps:\n  - label: M\n    matrix:\n      setup:\n        os: [linux, macos]\n"
                      "    command: make check OS={{matrix.os}}\n")
    job = jobs_of(yml)["m"]
    assert job["strategy"]["matrix"]["os"] == ["linux", "macos"]
    assert any(s.get("run") == "make check OS=${{ matrix.os }}" for s in job["steps"])


def test_single_dimension_matrix_uses_value(tmp_path):
    _, yml = run_file(tmp_path,
                      "steps:\n  - label: M\n    matrix: ['3.11', '3.12']\n"
                      "    command: pytest -V {{matrix}}\n")
    job = jobs_of(yml)["m"]
    assert job["strategy"]["matrix"]["value"] == ["3.11", "3.12"]
    assert any(s.get("run") == "pytest -V ${{ matrix.value }}" for s in job["steps"])


def test_soft_fail_and_timeout(tmp_path):
    _, yml = run_file(tmp_path,
                      "steps:\n  - label: L\n    soft_fail: true\n    timeout_in_minutes: 20\n"
                      "    command: make lint\n")
    job = jobs_of(yml)["l"]
    assert job["continue-on-error"] is True
    assert job["timeout-minutes"] == 20


def test_soft_fail_exit_status_is_flagged(tmp_path):
    report, _ = run_file(tmp_path,
                         "steps:\n  - label: L\n    command: make\n"
                         "    soft_fail:\n      - exit_status: 2\n")
    assert any(h.mapping_id == "step-settings" and h.manual and "exit" in h.source.lower()
               for h in report.hits)


def test_artifact_paths_upload_always(tmp_path):
    _, yml = run_file(tmp_path,
                      "steps:\n  - label: B\n    command: make\n    artifact_paths: ['dist/**']\n")
    upload = next(s for s in jobs_of(yml)["b"]["steps"]
                  if s.get("uses", "").startswith("actions/upload-artifact"))
    assert upload["if"] == "always()"  # Buildkite uploads even on failure


def test_branches_filter_with_exclusion(tmp_path):
    _, yml = run_file(tmp_path,
                      "steps:\n  - label: D\n    command: make\n    branches: 'main !release/*'\n")
    condition = jobs_of(yml)["d"]["if"]
    assert "github.ref_name == 'main'" in condition
    assert "!(startsWith(github.ref_name, 'release/'))" in condition


def test_agents_queue_becomes_self_hosted_labels(tmp_path):
    report, yml = run_file(tmp_path,
                           "steps:\n  - label: B\n    command: make\n    agents:\n      queue: builders\n")
    assert jobs_of(yml)["b"]["runs-on"] == ["self-hosted", "builders"]
    assert any(h.mapping_id == "agents" and h.manual for h in report.hits)


# --- plugins ---

def test_docker_plugin_becomes_container(tmp_path):
    _, yml = run_file(tmp_path,
                      "steps:\n  - label: B\n    command: make\n"
                      "    plugins:\n      - docker#v5.10.0:\n          image: python:3.12\n")
    assert jobs_of(yml)["b"]["container"] == "python:3.12"


def test_unknown_plugin_is_flagged_not_dropped(tmp_path):
    report, yml = run_file(tmp_path,
                           "steps:\n  - label: B\n    command: make\n"
                           "    plugins:\n      - some/vendor-plugin#v1.0.0:\n          setting: x\n")
    assert any(h.mapping_id == "plugins" and h.manual for h in report.hits)
    assert "TODO" in yml


# --- variables ---

def test_variables_defined_only_when_used(tmp_path):
    _, yml = run_file(tmp_path, "steps:\n  - label: B\n    command: echo $BUILDKITE_COMMIT\n")
    env = yaml.safe_load(yml)["env"]
    assert env["BUILDKITE_COMMIT"] == "${{ github.sha }}"
    assert "BUILDKITE_BUILD_ID" not in env


def test_buildkite_agent_cli_is_flagged(tmp_path):
    report, _ = run_file(tmp_path,
                         "steps:\n  - label: B\n    command: buildkite-agent artifact upload dist/**\n")
    assert any(h.mapping_id == "variables" and h.manual and "buildkite-agent" in h.source
               for h in report.hits)


def test_parallel_job_var_not_double_flagged(tmp_path):
    report, _ = run_file(tmp_path,
                         "steps:\n  - label: T\n    parallelism: 2\n"
                         "    command: pytest --shard $BUILDKITE_PARALLEL_JOB\n")
    # the matrix mapping already defines it, so it must not be reported as missing
    assert not any(h.mapping_id == "variables" and h.manual and "PARALLEL_JOB" in h.source
                   for h in report.hits)


# --- full example ---

def test_full_example_kitchen_sink(tmp_path):
    report, yml = run_file(tmp_path, EXAMPLE.read_text())
    jobs = jobs_of(yml)
    assert list(jobs) == ["build", "unit", "lint", "matrix-build", "gate", "deploy"]
    assert jobs["unit"]["needs"] == "build"
    assert jobs["gate"]["needs"] == ["unit", "lint", "matrix-build"]
    assert jobs["deploy"]["needs"] == "gate"
    assert jobs["deploy"]["if"] == "github.ref_name == 'main' && github.ref_type != 'tag'"
    assert jobs["build"]["container"] == "python:3.12"
    assert not report.unmapped


def test_no_internal_keys_leak(tmp_path):
    report, yml = run_file(tmp_path, EXAMPLE.read_text())
    for private in ("_script", "_pre_steps", "_post_steps", "_artifacts", "_explicit_needs"):
        assert private not in yml, private


def test_full_example_is_valid_gha(tmp_path):
    _, yml = run_file(tmp_path, EXAMPLE.read_text())
    doc = yaml.safe_load(yml)
    jobs = doc["jobs"]
    for jid, job in jobs.items():
        needs = job.get("needs", [])
        for dep in ([needs] if isinstance(needs, str) else needs):
            assert dep in jobs, f"{jid}: dangling needs {dep}"
        for step in job["steps"]:
            assert ("run" in step) or ("uses" in step), (jid, step)


def test_anchor_is_reported(tmp_path):
    report, yml = run_file(tmp_path, "steps:\n  - &base\n    label: A\n    command: make\n")
    assert not yml
    assert any(h.mapping_id == "parse" and h.manual for h in report.hits)
