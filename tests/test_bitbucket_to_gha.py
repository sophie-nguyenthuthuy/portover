from pathlib import Path

import yaml

from portover.migrations import get

MIG = get("bitbucket-to-gha")
EXAMPLE = Path(__file__).parent.parent / "examples" / "bitbucket" / "bitbucket-pipelines.yml"


def run_file(tmp_path, text):
    (tmp_path / "bitbucket-pipelines.yml").write_text(text)
    return MIG.run(tmp_path)


def doc_of(report, name="default"):
    return yaml.safe_load(report.outputs[f".github/workflows/{name}.yml"])


def on_of(doc):
    return doc.get("on", doc.get(True))  # PyYAML reads a bare `on:` key as True


def steps_pipeline(*commands):
    """One step whose script runs all the given commands."""
    body = "".join(f"          - {c}\n" for c in commands)
    return "pipelines:\n  default:\n    - step:\n        script:\n" + body


# --- the core mapping: a Bitbucket step is a GHA job ---

def test_each_step_becomes_a_job_chained_sequentially(tmp_path):
    report = run_file(tmp_path,
                      "pipelines:\n  default:\n"
                      "    - step:\n        name: Build\n        script: [make build]\n"
                      "    - step:\n        name: Test\n        script: [make test]\n")
    jobs = doc_of(report)["jobs"]
    assert list(jobs) == ["build", "test"]
    assert "needs" not in jobs["build"]
    assert jobs["test"]["needs"] == "build"  # steps are sequential in Bitbucket


def test_script_commands_become_run_steps(tmp_path):
    report = run_file(tmp_path, steps_pipeline("make a", "make b"))
    steps = doc_of(report)["jobs"]["step-1"]["steps"]
    assert steps[0] == {"uses": "actions/checkout@v4"}
    assert [s["run"] for s in steps if "run" in s] == ["make a", "make b"]


def test_parallel_block_fans_out_and_back_in(tmp_path):
    report = run_file(tmp_path,
                      "pipelines:\n  default:\n"
                      "    - step:\n        name: Build\n        script: [make]\n"
                      "    - parallel:\n"
                      "        - step:\n            name: Unit\n            script: [make unit]\n"
                      "        - step:\n            name: Lint\n            script: [make lint]\n"
                      "    - step:\n        name: Ship\n        script: [make ship]\n")
    jobs = doc_of(report)["jobs"]
    assert jobs["unit"]["needs"] == "build" and jobs["lint"]["needs"] == "build"
    assert jobs["ship"]["needs"] == ["unit", "lint"]


def test_after_script_runs_always(tmp_path):
    report = run_file(tmp_path,
                      "pipelines:\n  default:\n    - step:\n        script: [make]\n"
                      "        after-script: [./report.sh]\n")
    steps = doc_of(report)["jobs"]["step-1"]["steps"]
    assert {"if": "always()", "run": "./report.sh"} in steps


# --- artifacts: Bitbucket's implicit pass-through ---

def test_artifacts_upload_and_auto_download_downstream(tmp_path):
    report = run_file(tmp_path,
                      "pipelines:\n  default:\n"
                      "    - step:\n        name: Build\n        script: [make]\n"
                      "        artifacts: [dist/**]\n"
                      "    - step:\n        name: Deploy\n        script: [./deploy.sh]\n")
    jobs = doc_of(report)["jobs"]
    assert {"uses": "actions/upload-artifact@v4",
            "with": {"name": "build", "path": "dist/**"}} in jobs["build"]["steps"]
    # GHA passes nothing between jobs, so the download must be inserted
    assert {"uses": "actions/download-artifact@v4", "with": {"name": "build"}} in jobs["deploy"]["steps"]


def test_download_false_opts_out(tmp_path):
    report = run_file(tmp_path,
                      "pipelines:\n  default:\n"
                      "    - step:\n        name: Build\n        script: [make]\n        artifacts: [dist/**]\n"
                      "    - step:\n        name: Deploy\n        script: [./d.sh]\n"
                      "        artifacts:\n          download: false\n          paths: [out/**]\n")
    deploy = doc_of(report)["jobs"]["deploy"]
    assert all(s.get("uses") != "actions/download-artifact@v4" for s in deploy["steps"])


def test_no_internal_keys_leak_into_output(tmp_path):
    report = run_file(tmp_path, EXAMPLE.read_text())
    for content in report.outputs.values():
        for private in ("_pre_steps", "_post_steps", "_script", "_artifacts",
                        "_after_script", "_checkout_with", "_no_download", "_no_checkout"):
            assert private not in content, private


# --- trigger sections become separate workflow files ---

def test_sections_become_separate_workflows(tmp_path):
    report = run_file(tmp_path,
                      "pipelines:\n"
                      "  default:\n    - step:\n        script: [make]\n"
                      "  branches:\n    main:\n      - step:\n          script: [./deploy.sh]\n"
                      "  tags:\n    'v*':\n      - step:\n          script: [./release.sh]\n"
                      "  pull-requests:\n    '**':\n      - step:\n          script: [make test]\n")
    paths = set(report.outputs)
    assert paths == {".github/workflows/default.yml", ".github/workflows/branches-main.yml",
                     ".github/workflows/tags-v.yml", ".github/workflows/pull-requests.yml"}
    assert on_of(doc_of(report, "branches-main"))["push"]["branches"] == ["main"]
    assert "pull_request" in on_of(doc_of(report, "pull-requests"))


def test_custom_pipeline_becomes_workflow_dispatch(tmp_path):
    report = run_file(tmp_path,
                      "pipelines:\n  custom:\n    release:\n"
                      "      - variables:\n          - name: version\n            default: patch\n"
                      "      - step:\n          script: [./release.sh $version]\n")
    doc = doc_of(report, "custom-release")
    assert on_of(doc)["workflow_dispatch"]["inputs"]["version"]["default"] == "patch"
    # the script still says $version, so it must exist as env
    assert doc["env"]["version"] == "${{ inputs.version }}"


# --- step fields ---

def test_deployment_and_manual_trigger(tmp_path):
    report = run_file(tmp_path,
                      "pipelines:\n  default:\n    - step:\n        deployment: production\n"
                      "        trigger: manual\n        script: [./deploy.sh]\n")
    assert doc_of(report)["jobs"]["step-1"]["environment"] == "production"
    assert any(h.mapping_id == "deployment" and h.manual for h in report.hits)


def test_oidc_and_max_time(tmp_path):
    report = run_file(tmp_path,
                      "pipelines:\n  default:\n    - step:\n        oidc: true\n"
                      "        max-time: 15\n        script: [make]\n")
    job = doc_of(report)["jobs"]["step-1"]
    assert job["permissions"]["id-token"] == "write"
    assert job["timeout-minutes"] == 15


def test_named_cache_expands_to_path_and_key(tmp_path):
    report = run_file(tmp_path,
                      "pipelines:\n  default:\n    - step:\n        caches: [pip]\n        script: [make]\n")
    cache = next(s for s in doc_of(report)["jobs"]["step-1"]["steps"]
                 if s.get("uses", "").startswith("actions/cache"))
    assert cache["with"]["path"] == "~/.cache/pip"
    assert "hashFiles" in cache["with"]["key"]


def test_service_resolved_from_definitions(tmp_path):
    report = run_file(tmp_path,
                      "definitions:\n  services:\n    postgres:\n      image: postgres:16\n"
                      "      variables:\n        POSTGRES_PASSWORD: secret\n"
                      "pipelines:\n  default:\n    - step:\n        services: [postgres]\n        script: [make]\n")
    services = doc_of(report)["jobs"]["step-1"]["services"]
    assert services["postgres"]["image"] == "postgres:16"
    assert services["postgres"]["env"]["POSTGRES_PASSWORD"] == "secret"


def test_global_image_and_clone_applied_to_every_job(tmp_path):
    report = run_file(tmp_path,
                      "image: python:3.12\nclone:\n  depth: full\n"
                      + steps_pipeline("make a") )
    job = doc_of(report)["jobs"]["step-1"]
    assert job["container"] == "python:3.12"
    assert job["steps"][0]["with"]["fetch-depth"] == 0


# --- variables ---

def test_bitbucket_vars_defined_only_when_used(tmp_path):
    report = run_file(tmp_path, steps_pipeline("echo $BITBUCKET_COMMIT"))
    env = doc_of(report)["env"]
    assert env["BITBUCKET_COMMIT"] == "${{ github.sha }}"
    assert "BITBUCKET_PR_ID" not in env  # unused ones are not invented


def test_exit_code_var_flagged_not_faked(tmp_path):
    report = run_file(tmp_path,
                      "pipelines:\n  default:\n    - step:\n        script: [make]\n"
                      "        after-script: [echo $BITBUCKET_EXIT_CODE]\n")
    assert any(h.mapping_id == "variables" and h.manual and "EXIT_CODE" in h.source
               for h in report.hits)


# --- pipes ---

def test_unknown_pipe_is_flagged_not_dropped(tmp_path):
    report = run_file(tmp_path,
                      "pipelines:\n  default:\n    - step:\n        script:\n"
                      "          - pipe: some/unknown-pipe:1.0\n")
    assert any(h.mapping_id == "pipe" and h.manual for h in report.hits)
    assert "TODO" in report.outputs[".github/workflows/default.yml"]


def test_pipe_credential_variable_becomes_secret(tmp_path):
    report = run_file(tmp_path,
                      "pipelines:\n  default:\n    - step:\n        script:\n"
                      "          - pipe: atlassian/slack-notify:2.0.0\n"
                      "            variables:\n              WEBHOOK_URL: $SLACK_WEBHOOK\n")
    content = report.outputs[".github/workflows/default.yml"]
    assert "${{ secrets.SLACK_WEBHOOK }}" in content


# --- full example ---

def test_full_example_kitchen_sink(tmp_path):
    report = run_file(tmp_path, EXAMPLE.read_text())
    assert set(report.outputs) == {
        ".github/workflows/default.yml", ".github/workflows/branches-main.yml",
        ".github/workflows/pull-requests.yml", ".github/workflows/custom-release.yml"}
    jobs = doc_of(report)["jobs"]
    assert list(jobs) == ["build", "unit-tests", "lint", "publish"]
    assert jobs["publish"]["needs"] == ["unit-tests", "lint"]
    assert not report.unmapped


def test_full_example_is_valid_gha(tmp_path):
    report = run_file(tmp_path, EXAMPLE.read_text())
    for path, content in report.outputs.items():
        doc = yaml.safe_load(content)
        assert doc.get("on", doc.get(True)), path
        for jid, job in doc["jobs"].items():
            needs = job.get("needs", [])
            for dep in ([needs] if isinstance(needs, str) else needs):
                assert dep in doc["jobs"], f"{path} {jid}: dangling needs {dep}"
            for step in job["steps"]:
                assert ("run" in step) or ("uses" in step), (path, jid, step)


def test_anchor_is_reported(tmp_path):
    report = run_file(tmp_path, "definitions:\n  steps:\n    - step: &build\n        script: [make]\n")
    assert not report.outputs
    assert any(h.mapping_id == "parse" and h.manual for h in report.hits)
