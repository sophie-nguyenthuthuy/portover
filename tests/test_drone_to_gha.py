from pathlib import Path

import yaml

from portover.migrations import get
from portover.miniyaml import parse_all

MIG = get("drone-to-gha")
EXAMPLE = Path(__file__).parent.parent / "examples" / "drone" / ".drone.yml"


def run_file(tmp_path, text):
    (tmp_path / ".drone.yml").write_text(text)
    report = MIG.run(tmp_path)
    return report, report.outputs.get(".github/workflows/ci.yml", "")


def jobs_of(yml):
    return yaml.safe_load(yml)["jobs"]


def pipeline(*steps, **top):
    body = "".join(
        f"  - name: {n}\n    image: {i}\n    commands:\n      - {c}\n" for n, i, c in steps)
    head = "kind: pipeline\nname: default\n"
    for key, value in top.items():
        head += f"{key}: {value}\n"
    return head + "steps:\n" + body


# --- multi-document parsing ---

def test_parse_all_splits_documents():
    docs = parse_all("kind: pipeline\nname: a\n---\nkind: pipeline\nname: b\n")
    assert [d["name"] for d in docs] == ["a", "b"]


def test_parse_all_does_not_merge_keys():
    docs = parse_all("name: a\nsteps: [1]\n---\nname: b\n")
    assert len(docs) == 2 and docs[1] == {"name": "b"}  # not merged over the first


def test_multiple_pipelines_become_multiple_jobs(tmp_path):
    _, yml = run_file(tmp_path,
                      "kind: pipeline\nname: one\nsteps:\n  - name: a\n    image: alpine\n"
                      "    commands: [make a]\n"
                      "---\n"
                      "kind: pipeline\nname: two\ndepends_on: [one]\nsteps:\n  - name: b\n"
                      "    image: alpine\n    commands: [make b]\n")
    jobs = jobs_of(yml)
    assert list(jobs) == ["one", "two"]
    assert jobs["two"]["needs"] == "one"


# --- the container strategy ---

def test_shared_image_becomes_job_container(tmp_path):
    _, yml = run_file(tmp_path, pipeline(("build", "golang:1.22", "go build"),
                                         ("test", "golang:1.22", "go test ./...")))
    job = jobs_of(yml)["default"]
    assert job["container"] == "golang:1.22"
    assert [s["run"].strip() for s in job["steps"] if "run" in s] == ["go build", "go test ./..."]


def test_differing_images_use_docker_run_with_workspace(tmp_path):
    report, yml = run_file(tmp_path, pipeline(("build", "golang:1.22", "go build"),
                                              ("lint", "golangci/golangci-lint", "golangci-lint run")))
    job = jobs_of(yml)["default"]
    assert "container" not in job  # a docker run inside a job container has no daemon
    build = next(s for s in job["steps"] if s.get("name") == "build")
    assert "docker run" in build["run"] and '-v "$PWD":/drone/src' in build["run"]
    assert any(h.mapping_id == "steps" and h.manual for h in report.hits)


def test_heredoc_terminator_dedents_to_column_zero(tmp_path):
    _, yml = run_file(tmp_path, pipeline(("a", "alpine", "echo one"), ("b", "busybox", "echo two")))
    run = next(s for s in jobs_of(yml)["default"]["steps"] if s.get("name") == "a")["run"]
    assert any(line == "DRONE_STEP" for line in run.splitlines()), run


def test_commands_stay_one_block(tmp_path):
    _, yml = run_file(tmp_path,
                      "kind: pipeline\nname: default\nsteps:\n  - name: a\n    image: alpine\n"
                      "    commands:\n      - cd sub\n      - make\n")
    # one run block keeps `cd` effective for the next line
    runs = [s["run"] for s in jobs_of(yml)["default"]["steps"] if "run" in s]
    assert runs == ["cd sub\nmake\n"]


# --- secrets ---

def test_from_secret_becomes_github_secret(tmp_path):
    report, yml = run_file(tmp_path,
                           "kind: pipeline\nname: default\nsteps:\n  - name: a\n    image: alpine\n"
                           "    environment:\n      TOKEN:\n        from_secret: api_token\n"
                           "    commands: [deploy]\n")
    step = next(s for s in jobs_of(yml)["default"]["steps"] if s.get("name") == "a")
    assert step["env"]["TOKEN"] == "${{ secrets.API_TOKEN }}"
    assert any(h.mapping_id == "environment" and h.manual for h in report.hits)


def test_secret_document_is_flagged_not_converted(tmp_path):
    report, yml = run_file(tmp_path,
                           pipeline(("a", "alpine", "make"))
                           + "---\nkind: secret\nname: token\nget:\n  path: secret/data/x\n  name: y\n")
    assert list(jobs_of(yml)) == ["default"]  # the secret document produces no job
    assert any(h.mapping_id == "kind" and h.manual and "secret" in h.source for h in report.hits)


def test_signature_document_dropped(tmp_path):
    report, yml = run_file(tmp_path,
                           pipeline(("a", "alpine", "make")) + "---\nkind: signature\nhmac: abc123\n")
    assert list(jobs_of(yml)) == ["default"]
    assert any(h.mapping_id == "kind" and not h.manual and "signature" in h.source
               for h in report.hits)


# --- conditions ---

def test_when_status_becomes_always(tmp_path):
    _, yml = run_file(tmp_path,
                      "kind: pipeline\nname: default\nsteps:\n  - name: a\n    image: alpine\n"
                      "    commands: [notify]\n    when:\n      status: [success, failure]\n")
    step = next(s for s in jobs_of(yml)["default"]["steps"] if s.get("name") == "a")
    assert step["if"].startswith("always()")  # must lead, or the step skips after a failure


def test_when_branch_and_event(tmp_path):
    _, yml = run_file(tmp_path,
                      "kind: pipeline\nname: default\nsteps:\n  - name: a\n    image: alpine\n"
                      "    commands: [make]\n    when:\n      branch: [main]\n      event: [push]\n")
    step = next(s for s in jobs_of(yml)["default"]["steps"] if s.get("name") == "a")
    assert "github.ref_name == 'main'" in step["if"]
    assert "github.event_name == 'push'" in step["if"]


def test_trigger_tag_event_adds_tag_trigger(tmp_path):
    _, yml = run_file(tmp_path,
                      "kind: pipeline\nname: default\ntrigger:\n  event: [tag]\n"
                      "steps:\n  - name: a\n    image: alpine\n    commands: [make]\n")
    doc = yaml.safe_load(yml)
    on = doc.get("on", doc.get(True))
    assert on["push"]["tags"] == ["*"]  # without a tag trigger the job's if: could never fire
    assert jobs_of(yml)["default"]["if"] == "github.ref_type == 'tag'"


# --- plugins ---

def test_docker_plugin_becomes_build_push_action(tmp_path):
    report, yml = run_file(tmp_path,
                           "kind: pipeline\nname: default\nsteps:\n  - name: publish\n"
                           "    image: plugins/docker\n    settings:\n      repo: acme/app\n"
                           "      tags: latest\n")
    step = next(s for s in jobs_of(yml)["default"]["steps"] if s.get("name") == "publish")
    assert step["uses"] == "docker/build-push-action@v6"
    assert step["with"]["tags"] == "acme/app:latest"


def test_git_plugin_dropped_as_redundant(tmp_path):
    _, yml = run_file(tmp_path,
                      "kind: pipeline\nname: default\nsteps:\n  - name: clone\n"
                      "    image: plugins/git\n    settings:\n      depth: 50\n"
                      "  - name: a\n    image: alpine\n    commands: [make]\n")
    steps = jobs_of(yml)["default"]["steps"]
    assert sum(1 for s in steps if s.get("uses", "").startswith("actions/checkout")) == 1
    assert all(s.get("name") != "clone" for s in steps)


def test_unknown_plugin_is_flagged_not_dropped(tmp_path):
    report, yml = run_file(tmp_path,
                           "kind: pipeline\nname: default\nsteps:\n  - name: x\n"
                           "    image: plugins/unknown-thing\n    settings:\n      key: value\n")
    assert any(h.mapping_id == "settings" and h.manual for h in report.hits)
    assert "TODO" in yml


# --- other fields ---

def test_services_get_healthcheck(tmp_path):
    _, yml = run_file(tmp_path,
                      "kind: pipeline\nname: default\nservices:\n  - name: db\n    image: postgres:16\n"
                      "steps:\n  - name: a\n    image: alpine\n    commands: [make]\n")
    service = jobs_of(yml)["default"]["services"]["db"]
    assert service["image"] == "postgres:16"
    assert "pg_isready" in service["options"]


def test_failure_ignore_and_clone_depth(tmp_path):
    _, yml = run_file(tmp_path,
                      "kind: pipeline\nname: default\nclone:\n  depth: 10\n"
                      "steps:\n  - name: a\n    image: alpine\n    failure: ignore\n    commands: [make]\n")
    job = jobs_of(yml)["default"]
    assert job["steps"][0]["with"]["fetch-depth"] == 10
    assert next(s for s in job["steps"] if s.get("name") == "a")["continue-on-error"] is True


def test_clone_disable_emits_no_checkout(tmp_path):
    _, yml = run_file(tmp_path,
                      "kind: pipeline\nname: default\nclone:\n  disable: true\n"
                      "steps:\n  - name: a\n    image: alpine\n    commands: [make]\n")
    steps = jobs_of(yml)["default"]["steps"]
    assert all(not s.get("uses", "").startswith("actions/checkout") for s in steps)


def test_drone_vars_defined_only_when_used(tmp_path):
    _, yml = run_file(tmp_path, pipeline(("a", "alpine", "echo $DRONE_COMMIT_SHA")))
    env = yaml.safe_load(yml)["env"]
    assert env["DRONE_COMMIT_SHA"] == "${{ github.sha }}"
    assert "DRONE_BUILD_NUMBER" not in env


def test_workspace_var_flagged_not_faked(tmp_path):
    report, _ = run_file(tmp_path, pipeline(("a", "alpine", "ls $DRONE_WORKSPACE")))
    assert any(h.mapping_id == "variables" and h.manual and "WORKSPACE" in h.source
               for h in report.hits)


# --- full example ---

def test_full_example_kitchen_sink(tmp_path):
    report, yml = run_file(tmp_path, EXAMPLE.read_text())
    jobs = jobs_of(yml)
    assert list(jobs) == ["default", "publish"]
    assert jobs["publish"]["needs"] == "default"
    assert jobs["publish"]["if"] == "github.ref_type == 'tag'"
    assert "pg_isready" in jobs["default"]["services"]["database"]["options"]
    assert not report.unmapped


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
    for private in ("_steps", "_checkout_with", "_no_checkout", "_skip"):
        assert private not in yml, private
