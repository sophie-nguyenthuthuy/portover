from pathlib import Path

from portover.migrations import get
from portover.migrations.jenkins_to_gha.parser import parse

MIG = get("jenkins-to-gha")
EXAMPLE = Path(__file__).parent.parent / "examples" / "jenkins" / "Jenkinsfile"


def run_file(tmp_path, text):
    (tmp_path / "Jenkinsfile").write_text(text)
    report = MIG.run(tmp_path)
    return report, report.outputs.get(".github/workflows/ci.yml", "")


def test_parser_nested_blocks():
    tree = parse("pipeline {\n  stages {\n    stage('B') { steps { sh 'make' } }\n  }\n}\n")
    pipeline = tree.child("pipeline")
    stage = pipeline.child("stages").children[0]
    assert stage.header == "stage('B')"
    assert stage.child("steps").stmts == ["sh 'make'"]


def test_parser_ignores_comments_and_strings():
    tree = parse("pipeline { // comment { brace\n  agent any\n  /* block { */ stages { }\n}\n")
    assert tree.child("pipeline").stmts == ["agent any"]


def test_stages_become_chained_jobs(tmp_path):
    _, yml = run_file(tmp_path, "pipeline {\n agent any\n stages {\n"
                      "  stage('Build') { steps { sh 'make build' } }\n"
                      "  stage('Test') { steps { sh 'make test' } }\n } }\n")
    assert "build:" in yml and "test:" in yml
    assert "needs: build" in yml
    assert "run: make build" in yml
    assert "uses: actions/checkout@v4" in yml


def test_docker_agent_becomes_container(tmp_path):
    _, yml = run_file(tmp_path, "pipeline {\n agent { docker { image 'python:3.12' } }\n"
                      " stages { stage('B') { steps { sh 'make' } } } }\n")
    assert "container: python:3.12" in yml


def test_parallel_stages_share_needs(tmp_path):
    _, yml = run_file(tmp_path, "pipeline {\n agent any\n stages {\n"
                      "  stage('Build') { steps { sh 'make' } }\n"
                      "  stage('Test') { parallel {\n"
                      "    stage('unit') { steps { sh 'make unit' } }\n"
                      "    stage('lint') { steps { sh 'make lint' } }\n  } }\n"
                      "  stage('Deploy') { steps { sh 'make deploy' } }\n } }\n")
    assert "unit:" in yml and "lint:" in yml
    assert yml.count("needs: build") == 2
    assert "- unit" in yml and "- lint" in yml  # deploy needs both


def test_when_branch_becomes_if(tmp_path):
    _, yml = run_file(tmp_path, "pipeline {\n agent any\n stages {\n"
                      "  stage('Deploy') { when { branch 'main' } steps { sh './d.sh' } }\n } }\n")
    assert "if: github.ref == 'refs/heads/main'" in yml


def test_credentials_become_secrets(tmp_path):
    report, yml = run_file(tmp_path, "pipeline {\n agent any\n"
                           " environment { TOKEN = credentials('api-token') }\n"
                           " stages { stage('B') { steps { sh 'make' } } } }\n")
    assert "secrets.API_TOKEN" in yml
    assert any(h.mapping_id == "environment" and h.manual for h in report.hits)


def test_post_failure_job(tmp_path):
    _, yml = run_file(tmp_path, "pipeline {\n agent any\n"
                      " stages { stage('B') { steps { sh 'make' } } }\n"
                      " post { failure { sh './notify.sh' } } }\n")
    assert "post:" in yml
    assert "if: always()" in yml
    assert "contains(needs.*.result, 'failure')" in yml


def test_full_example_kitchen_sink(tmp_path):
    report, yml = run_file(tmp_path, EXAMPLE.read_text())
    for expected in ("container: python:3.12", "REGISTRY: ghcr.io/acme", "timeout-minutes: 30",
                     "schedule", "workflow_dispatch", "setup-java", "setup-node",
                     "run: make build", "needs: build", "concurrency"):
        assert expected in yml, f"missing {expected!r}\n{yml}"
    assert not any("stage" in u for u in report.unmapped)


def test_scripted_pipeline_flagged(tmp_path):
    report, yml = run_file(tmp_path, "node {\n  sh 'make'\n}\n")
    assert yml == ""
    assert any(h.mapping_id == "scripted" for h in report.hits)
