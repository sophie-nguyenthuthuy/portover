from pathlib import Path

import yaml

from portover.migrations import get

MIG = get("woodpecker-to-gha")
EXAMPLE_DIR = Path(__file__).parent.parent / "examples" / "woodpecker"


def run_file(tmp_path, text, name=".woodpecker.yml"):
    path = tmp_path / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    report = MIG.run(tmp_path)
    return report, report.outputs.get(".github/workflows/ci.yml", "")


def doc_of(yml):
    return yaml.safe_load(yml)


def on_of(doc):
    return doc.get("on", doc.get(True))  # PyYAML reads a bare `on:` key as True


def jobs_of(yml):
    return doc_of(yml)["jobs"]


# --- the shapes Woodpecker accepts that Drone does not ---

def test_steps_list_form(tmp_path):
    _, yml = run_file(tmp_path,
                      "steps:\n  - name: build\n    image: alpine\n    commands: [make]\n")
    steps = jobs_of(yml)["woodpecker"]["steps"]
    assert any(s.get("name") == "build" for s in steps)


def test_steps_map_form(tmp_path):
    _, yml = run_file(tmp_path,
                      "steps:\n  build:\n    image: alpine\n    commands: [make]\n")
    steps = jobs_of(yml)["woodpecker"]["steps"]
    assert any(s.get("name") == "build" and s.get("run", "").strip() == "make" for s in steps)


def test_environment_list_form(tmp_path):
    _, yml = run_file(tmp_path,
                      "steps:\n  - name: a\n    image: alpine\n"
                      "    environment:\n      - GOOS=linux\n      - CGO_ENABLED=0\n"
                      "    commands: [make]\n")
    step = next(s for s in jobs_of(yml)["woodpecker"]["steps"] if s.get("name") == "a")
    assert step["env"] == {"GOOS": "linux", "CGO_ENABLED": "0"}


def test_old_pipeline_key_is_accepted_and_flagged(tmp_path):
    report, yml = run_file(tmp_path,
                           "pipeline:\n  build:\n    image: alpine\n    commands: [make]\n")
    assert any(s.get("name") == "build" for s in jobs_of(yml)["woodpecker"]["steps"])
    assert any(h.mapping_id == "steps" and h.manual and "pipeline" in h.source for h in report.hits)


# --- when: is a list of OR'd condition sets ---

def test_when_sets_are_ored_and_keys_anded(tmp_path):
    _, yml = run_file(tmp_path,
                      "when:\n  - event: push\n    branch: main\n  - event: tag\n"
                      "steps:\n  - name: a\n    image: alpine\n    commands: [make]\n")
    condition = jobs_of(yml)["woodpecker"]["if"]
    assert "(github.event_name == 'push' && github.ref_name == 'main')" in condition
    assert "||" in condition and "github.ref_type == 'tag'" in condition


def test_when_map_form_is_one_set(tmp_path):
    _, yml = run_file(tmp_path,
                      "when:\n  event: push\n  branch: main\n"
                      "steps:\n  - name: a\n    image: alpine\n    commands: [make]\n")
    condition = jobs_of(yml)["woodpecker"]["if"]
    assert "||" not in condition


def test_step_when_status_becomes_always(tmp_path):
    _, yml = run_file(tmp_path,
                      "steps:\n  - name: a\n    image: alpine\n    commands: [make]\n"
                      "  - name: notify\n    image: alpine\n    commands: [./n.sh]\n"
                      "    when:\n      - status: [success, failure]\n")
    step = next(s for s in jobs_of(yml)["woodpecker"]["steps"] if s.get("name") == "notify")
    assert step["if"].startswith("always()")


def test_push_and_tag_events_keep_branch_pushes_working(tmp_path):
    _, yml = run_file(tmp_path,
                      "when:\n  - event: push\n  - event: tag\n"
                      "steps:\n  - name: a\n    image: alpine\n    commands: [make]\n")
    push = on_of(doc_of(yml))["push"]
    # `tags:` alone would mean ONLY tags trigger, silently stopping branch builds
    assert push["tags"] == ["*"] and push["branches"] == ["**"]


# --- matrix ---

def test_matrix_axes_and_env_passthrough(tmp_path):
    _, yml = run_file(tmp_path,
                      "matrix:\n  GO_VERSION:\n    - '1.21'\n    - '1.22'\n"
                      "steps:\n  - name: a\n    image: alpine\n    commands: [go test -v $GO_VERSION]\n")
    job = jobs_of(yml)["woodpecker"]
    assert job["strategy"]["matrix"]["GO_VERSION"] == ["1.21", "1.22"]
    # Woodpecker exposes matrix values as env vars, so $GO_VERSION must resolve
    assert job["env"]["GO_VERSION"] == "${{ matrix.GO_VERSION }}"


def test_matrix_interpolated_into_image(tmp_path):
    _, yml = run_file(tmp_path,
                      "matrix:\n  GO_VERSION: ['1.21', '1.22']\n"
                      "steps:\n  - name: a\n    image: golang:${GO_VERSION}\n    commands: [make]\n")
    # container: is evaluated by GHA, not a shell, so it needs the expression form
    assert jobs_of(yml)["woodpecker"]["container"] == "golang:${{ matrix.GO_VERSION }}"


def test_matrix_include_rows(tmp_path):
    _, yml = run_file(tmp_path,
                      "matrix:\n  GO_VERSION: ['1.22']\n  include:\n    - GO_VERSION: '1.20'\n      TAG: legacy\n"
                      "steps:\n  - name: a\n    image: alpine\n    commands: [make]\n")
    matrix = jobs_of(yml)["woodpecker"]["strategy"]["matrix"]
    assert matrix["include"] == [{"GO_VERSION": "1.20", "TAG": "legacy"}]


# --- multi-file workflows ---

def test_workflow_directory_files_become_jobs_with_needs(tmp_path):
    (tmp_path / ".woodpecker").mkdir()
    (tmp_path / ".woodpecker" / "build.yaml").write_text(
        "steps:\n  - name: a\n    image: alpine\n    commands: [make]\n")
    (tmp_path / ".woodpecker" / "publish.yaml").write_text(
        "depends_on: [build]\nsteps:\n  - name: b\n    image: alpine\n    commands: [make ship]\n")
    report = MIG.run(tmp_path)
    jobs = jobs_of(report.outputs[".github/workflows/ci.yml"])
    assert list(jobs) == ["build", "publish"]
    assert jobs["publish"]["needs"] == "build"


# --- images and secrets ---

def test_shared_image_becomes_container(tmp_path):
    _, yml = run_file(tmp_path,
                      "steps:\n  - name: a\n    image: golang:1.22\n    commands: [go build]\n"
                      "  - name: b\n    image: golang:1.22\n    commands: [go test]\n")
    job = jobs_of(yml)["woodpecker"]
    assert job["container"] == "golang:1.22"
    assert all("docker run" not in s.get("run", "") for s in job["steps"])


def test_differing_images_use_docker_run(tmp_path):
    report, yml = run_file(tmp_path,
                           "steps:\n  - name: a\n    image: golang:1.22\n    commands: [go build]\n"
                           "  - name: b\n    image: alpine\n    commands: [sh ./x.sh]\n")
    job = jobs_of(yml)["woodpecker"]
    assert "container" not in job
    step = next(s for s in job["steps"] if s.get("name") == "a")
    assert "docker run" in step["run"] and '-v "$PWD":/woodpecker/src' in step["run"]
    assert any(line == "WOODPECKER_STEP" for line in step["run"].splitlines())


def test_from_secret_and_legacy_secrets_list(tmp_path):
    report, yml = run_file(tmp_path,
                           "steps:\n  - name: a\n    image: alpine\n    commands: [deploy]\n"
                           "    environment:\n      TOKEN:\n        from_secret: api_token\n"
                           "  - name: b\n    image: alpine\n    commands: [push]\n"
                           "    secrets: [docker_password]\n")
    steps = jobs_of(yml)["woodpecker"]["steps"]
    assert next(s for s in steps if s.get("name") == "a")["env"]["TOKEN"] == "${{ secrets.API_TOKEN }}"
    assert next(s for s in steps if s.get("name") == "b")["env"]["DOCKER_PASSWORD"] == (
        "${{ secrets.DOCKER_PASSWORD }}")


# --- other fields ---

def test_runs_on_statuses_are_not_runner_selection(tmp_path):
    _, yml = run_file(tmp_path,
                      "runs_on: [success, failure]\n"
                      "steps:\n  - name: a\n    image: alpine\n    commands: [make]\n")
    job = jobs_of(yml)["woodpecker"]
    assert job["if"] == "always()"
    assert job["runs-on"] == "ubuntu-latest"  # not affected by runs_on:


def test_labels_platform_maps_to_hosted_runner(tmp_path):
    _, yml = run_file(tmp_path,
                      "labels:\n  platform: linux/amd64\n"
                      "steps:\n  - name: a\n    image: alpine\n    commands: [make]\n")
    assert jobs_of(yml)["woodpecker"]["runs-on"] == "ubuntu-latest"


def test_clone_depth_and_skip_clone(tmp_path):
    _, yml = run_file(tmp_path,
                      "clone:\n  git:\n    settings:\n      depth: 10\n"
                      "steps:\n  - name: a\n    image: alpine\n    commands: [make]\n")
    assert jobs_of(yml)["woodpecker"]["steps"][0]["with"]["fetch-depth"] == 10
    _, yml2 = run_file(tmp_path, "skip_clone: true\n"
                       "steps:\n  - name: a\n    image: alpine\n    commands: [make]\n")
    assert all(not s.get("uses", "").startswith("actions/checkout")
               for s in jobs_of(yml2)["woodpecker"]["steps"])


def test_service_map_form_gets_healthcheck(tmp_path):
    _, yml = run_file(tmp_path,
                      "services:\n  database:\n    image: postgres:16\n"
                      "    environment:\n      - POSTGRES_PASSWORD=secret\n"
                      "steps:\n  - name: a\n    image: alpine\n    commands: [make]\n")
    service = jobs_of(yml)["woodpecker"]["services"]["database"]
    assert service["env"]["POSTGRES_PASSWORD"] == "secret"
    assert "pg_isready" in service["options"]


def test_ci_variables_defined_only_when_used(tmp_path):
    _, yml = run_file(tmp_path,
                      "steps:\n  - name: a\n    image: alpine\n    commands: [echo $CI_COMMIT_SHA]\n")
    env = doc_of(yml)["env"]
    assert env["CI_COMMIT_SHA"] == "${{ github.sha }}"
    assert "CI_PIPELINE_NUMBER" not in env


def test_unknown_ci_variable_is_reported_not_invented(tmp_path):
    report, _ = run_file(tmp_path,
                         "steps:\n  - name: a\n    image: alpine\n    commands: [echo $CI_MY_OWN_THING]\n")
    assert any(h.mapping_id == "ci-variables" and h.manual and "CI_MY_OWN_THING" in h.source
               for h in report.hits)


def test_docker_buildx_plugin(tmp_path):
    _, yml = run_file(tmp_path,
                      "steps:\n  - name: publish\n    image: woodpeckerci/plugin-docker-buildx\n"
                      "    settings:\n      repo: acme/app\n      tags: latest\n")
    step = next(s for s in jobs_of(yml)["woodpecker"]["steps"] if s.get("name") == "publish")
    assert step["uses"] == "docker/build-push-action@v6"
    assert step["with"]["tags"] == "acme/app:latest"


def test_unknown_plugin_flagged_not_dropped(tmp_path):
    report, yml = run_file(tmp_path,
                           "steps:\n  - name: x\n    image: woodpeckerci/plugin-mystery\n"
                           "    settings:\n      key: value\n")
    assert any(h.mapping_id == "settings" and h.manual for h in report.hits)
    assert "TODO" in yml


# --- full example ---

def test_full_example_kitchen_sink():
    report = MIG.run(EXAMPLE_DIR)
    yml = report.outputs[".github/workflows/ci.yml"]
    jobs = jobs_of(yml)
    assert list(jobs) == ["build", "publish"]
    assert jobs["publish"]["needs"] == "build"
    assert jobs["build"]["strategy"]["matrix"]["GO_VERSION"] == ["1.21", "1.22"]
    assert not report.unmapped


def test_full_example_is_valid_gha():
    report = MIG.run(EXAMPLE_DIR)
    yml = report.outputs[".github/workflows/ci.yml"]
    doc = doc_of(yml)
    assert on_of(doc)
    for jid, job in doc["jobs"].items():
        needs = job.get("needs", [])
        for dep in ([needs] if isinstance(needs, str) else needs):
            assert dep in doc["jobs"], f"{jid}: dangling needs {dep}"
        for step in job["steps"]:
            assert ("run" in step) or ("uses" in step), (jid, step)
    for private in ("_steps", "_checkout_with", "_no_checkout", "_skip"):
        assert private not in yml, private


def test_anchor_is_reported(tmp_path):
    report, yml = run_file(tmp_path,
                           "variables:\n  - &img alpine\nsteps:\n  - name: a\n    image: *img\n"
                           "    commands: [make]\n")
    assert not yml
    assert any(h.mapping_id == "parse" and h.manual for h in report.hits)
