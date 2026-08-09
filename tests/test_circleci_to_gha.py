from pathlib import Path

from portover.migrations import get

MIG = get("circleci-to-gha")
EXAMPLE = Path(__file__).parent.parent / "examples" / "circleci" / ".circleci" / "config.yml"


def run_file(tmp_path, text, filename="config.yml"):
    config = tmp_path / ".circleci" / filename
    config.parent.mkdir()
    config.write_text(text)
    report = MIG.run(tmp_path)
    return report


def test_detects_yml_and_yaml(tmp_path):
    config = tmp_path / ".circleci"
    config.mkdir()
    (config / "config.yaml").write_text("version: 2.1\n")
    assert MIG.detect(tmp_path) == [".circleci/config.yaml"]


def test_job_requires_filters_and_matrix(tmp_path):
    report = run_file(tmp_path, """version: 2.1
jobs:
  test:
    docker:
      - image: cimg/python:3.12
    steps:
      - checkout
      - run: pytest
workflows:
  ci:
    jobs:
      - test:
          matrix:
            parameters:
              python: ['3.11', '3.12']
          filters:
            branches:
              only: main
""")
    yml = report.outputs[".github/workflows/ci.yml"]
    assert "container: cimg/python:3.12" in yml
    assert "actions/checkout@v4" in yml
    assert "run: pytest" in yml
    assert "matrix:" in yml and '"3.11"' in yml
    assert "github.ref == 'refs/heads/main'" in yml
    assert not report.unmapped


def test_multiple_only_filters_are_or_not_and(tmp_path):
    report = run_file(tmp_path, """jobs:
  test:
    docker: [{image: cimg/base:current}]
    steps: [{run: make test}]
workflows:
  ci:
    jobs:
      - test:
          filters:
            branches:
              only: [main, develop]
""")
    yml = report.outputs[".github/workflows/ci.yml"]
    condition = next(line for line in yml.splitlines() if line.strip().startswith("if:"))
    assert " || " in condition
    assert "refs/heads/main" in condition and "refs/heads/develop" in condition


def test_approval_job_needs_no_definition(tmp_path):
    report = run_file(tmp_path, """jobs:
  build:
    machine: true
    steps:
      - run: make
workflows:
  ci:
    jobs:
      - build
      - hold:
          type: approval
          requires: [build]
""")
    yml = report.outputs[".github/workflows/ci.yml"]
    assert "hold:" in yml and "environment: approval" in yml and "needs: build" in yml
    assert any(h.manual and h.mapping_id == "workflows" for h in report.hits)


def test_reusable_command_arguments_are_substituted(tmp_path):
    report = run_file(tmp_path, """commands:
  greet:
    parameters:
      whom:
        type: string
        default: world
    steps:
      - run: echo << parameters.whom >>
jobs:
  hello:
    machine: true
    steps:
      - greet:
          whom: codex
workflows:
  ci:
    jobs: [hello]
""")
    yml = report.outputs[".github/workflows/ci.yml"]
    assert "run: echo codex" in yml
    assert "parameters.whom" not in yml


def test_circleci_20_without_workflows(tmp_path):
    report = run_file(tmp_path, """version: 2
jobs:
  build:
    machine: true
    steps:
      - run: make
""")
    assert ".github/workflows/ci.yml" in report.outputs
    assert "runs-on: ubuntu-latest" in report.outputs[".github/workflows/ci.yml"]
    assert any(h.mapping_id == "workflows" and h.manual for h in report.hits)
    assert "branches:" not in report.outputs[".github/workflows/ci.yml"]


def test_job_defaults_and_matrix_dimensions_are_merged(tmp_path):
    report = run_file(tmp_path, """jobs:
  test:
    machine: true
    shell: /bin/bash -eo pipefail
    working_directory: ~/project/app
    parallelism: 2
    parameters:
      python:
        type: string
    steps:
      - run: echo test
workflows:
  ci:
    jobs:
      - test:
          matrix:
            parameters:
              python: ['3.11', '3.12']
""")
    yml = report.outputs[".github/workflows/ci.yml"]
    assert "shell: bash" in yml and "working-directory: app" in yml
    assert "circle_node_index:" in yml and "python:" in yml


def test_workspace_root_is_preserved(tmp_path):
    report = run_file(tmp_path, """jobs:
  build:
    machine: true
    steps:
      - persist_to_workspace:
          root: output
          paths: [dist, reports]
workflows:
  ci:
    jobs: [build]
""")
    yml = report.outputs[".github/workflows/ci.yml"]
    assert "output/dist" in yml and "output/reports" in yml


def test_full_example_kitchen_sink(tmp_path):
    report = run_file(tmp_path, EXAMPLE.read_text())
    yml = report.outputs[".github/workflows/build-test-deploy.yml"]
    for expected in (
        "name: build-test-deploy", "container: cimg/python:3.12", "image: postgres:16",
        "APP_ENV: test", "actions/cache/restore@v4", "actions/cache/save@v4",
        "actions/upload-artifact@v4", "actions/download-artifact@v4", "timeout-minutes: 20",
        "runs-on: ubuntu-22.04", "needs: build", "schedule:", "cron: 0 3 * * *",
        "${{ inputs.deploy_env }}", "workflow_dispatch:",
    ):
        assert expected in yml, f"missing {expected!r}\n{yml}"
    assert any(h.mapping_id == "orb-steps" and h.manual for h in report.hits)
    assert not report.unmapped


def test_anchor_is_reported(tmp_path):
    report = run_file(tmp_path, "defaults: &defaults\n  docker: []\n")
    assert not report.outputs
    assert any(h.mapping_id == "parse" and h.manual for h in report.hits)
