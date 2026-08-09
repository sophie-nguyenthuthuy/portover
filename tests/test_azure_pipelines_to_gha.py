from pathlib import Path

import yaml

from portover.migrations import get
from portover.migrations.azure_pipelines_to_gha.expr import translate

MIG = get("azure-pipelines-to-gha")
EXAMPLE = Path(__file__).parent.parent / "examples" / "azure" / "azure-pipelines.yml"


def run_file(tmp_path, text):
    (tmp_path / "azure-pipelines.yml").write_text(text)
    report = MIG.run(tmp_path)
    return report, report.outputs.get(".github/workflows/ci.yml", "")


def jobs_of(yml):
    return yaml.safe_load(yml)["jobs"]


# --- condition translation ---

def test_translate_status_and_comparison():
    assert translate("succeeded()") == "success()"
    assert translate("failed()") == "failure()"
    assert translate("succeededOrFailed()") == "always()"
    assert translate("eq(variables['Build.SourceBranch'], 'refs/heads/main')") == (
        "github.ref == 'refs/heads/main'")


def test_translate_nested_functions():
    assert translate("and(succeeded(), eq(variables['Build.SourceBranch'], 'refs/heads/main'))") == (
        "(success() && github.ref == 'refs/heads/main')")
    assert translate("not(eq(variables['x'], 'y'))") == "!(env.x == 'y')"
    assert translate("or(failed(), canceled())") == "(failure() || cancelled())"


def test_translate_build_reason_to_event_name():
    assert translate("eq(variables['Build.Reason'], 'PullRequest')") == (
        "github.event_name == 'pull_request'")


def test_translate_gives_up_loudly():
    assert translate("format('{0}-{1}', variables.a, variables.b)") is None


# --- structure ---

def test_bare_steps_become_single_job(tmp_path):
    _, yml = run_file(tmp_path, "steps:\n  - script: make\n")
    jobs = jobs_of(yml)
    assert list(jobs) == ["build"]
    assert {"run": "make"} in jobs["build"]["steps"]


def test_checkout_added_unless_opted_out(tmp_path):
    _, yml = run_file(tmp_path, "steps:\n  - script: make\n")
    assert jobs_of(yml)["build"]["steps"][0] == {"uses": "actions/checkout@v4"}
    _, yml2 = run_file(tmp_path, "steps:\n  - checkout: none\n  - script: make\n")
    assert all(s.get("uses") != "actions/checkout@v4" for s in jobs_of(yml2)["build"]["steps"])


def test_stages_are_sequential_by_default(tmp_path):
    _, yml = run_file(tmp_path,
                      "stages:\n"
                      "  - stage: A\n    jobs:\n      - job: a\n        steps: [{script: make a}]\n"
                      "  - stage: B\n    jobs:\n      - job: b\n        steps: [{script: make b}]\n")
    jobs = jobs_of(yml)
    assert "needs" not in jobs["a"]
    assert jobs["b"]["needs"] == "a"  # implicit sequential stage dependency


def test_jobs_are_parallel_by_default(tmp_path):
    _, yml = run_file(tmp_path,
                      "jobs:\n"
                      "  - job: a\n    steps: [{script: make a}]\n"
                      "  - job: b\n    steps: [{script: make b}]\n")
    jobs = jobs_of(yml)
    assert "needs" not in jobs["a"] and "needs" not in jobs["b"]


def test_depends_on_becomes_needs(tmp_path):
    _, yml = run_file(tmp_path,
                      "jobs:\n"
                      "  - job: a\n    steps: [{script: make a}]\n"
                      "  - job: b\n    dependsOn: a\n    steps: [{script: make b}]\n")
    assert jobs_of(yml)["b"]["needs"] == "a"


# --- the macro/shell-substitution distinction ---

def test_predefined_macro_rewritten(tmp_path):
    _, yml = run_file(tmp_path, "steps:\n  - script: echo $(Build.SourceVersion)\n")
    runs = [s["run"] for s in jobs_of(yml)["build"]["steps"] if "run" in s]
    assert runs == ["echo ${{ github.sha }}"]


def test_shell_command_substitution_left_alone(tmp_path):
    _, yml = run_file(tmp_path, "steps:\n  - script: echo $(git rev-parse HEAD)\n")
    runs = [s["run"] for s in jobs_of(yml)["build"]["steps"] if "run" in s]
    assert runs == ["echo $(git rev-parse HEAD)"]  # NOT rewritten — it is bash, not an Azure macro


def test_declared_variable_macro_rewritten(tmp_path):
    _, yml = run_file(tmp_path, "variables:\n  myVar: hello\nsteps:\n  - script: echo $(myVar)\n")
    runs = [s["run"] for s in jobs_of(yml)["build"]["steps"] if "run" in s]
    assert runs == ["echo ${{ env.myVar }}"]


def test_staging_directory_flagged_not_faked(tmp_path):
    report, _ = run_file(tmp_path, "steps:\n  - script: ls $(Build.ArtifactStagingDirectory)\n")
    assert any(h.mapping_id == "predefined-variables" and h.manual for h in report.hits)


# --- tasks ---

def test_task_setup_and_artifacts(tmp_path):
    _, yml = run_file(tmp_path,
                      "steps:\n"
                      "  - task: UsePythonVersion@0\n    inputs:\n      versionSpec: '3.12'\n"
                      "  - task: PublishBuildArtifacts@1\n    inputs:\n"
                      "      pathToPublish: dist\n      artifactName: drop\n")
    steps = jobs_of(yml)["build"]["steps"]
    assert {"uses": "actions/setup-python@v5", "with": {"python-version": "3.12"}} in steps
    assert {"uses": "actions/upload-artifact@v4", "with": {"name": "drop", "path": "dist"}} in steps


def test_unknown_task_is_flagged_not_dropped(tmp_path):
    report, yml = run_file(tmp_path, "steps:\n  - task: SomeVendorThing@3\n")
    assert any(h.mapping_id == "task" and h.manual for h in report.hits)
    assert "TODO" in yml  # a visible placeholder, never a silent omission


def test_cli_task_becomes_run_step(tmp_path):
    _, yml = run_file(tmp_path,
                      "steps:\n  - task: DotNetCoreCLI@2\n    inputs:\n"
                      "      command: build\n      arguments: -c Release\n")
    runs = [s["run"] for s in jobs_of(yml)["build"]["steps"] if "run" in s]
    assert runs == ["dotnet build -c Release"]


def test_step_keys_ordered_uses_before_with(tmp_path):
    _, yml = run_file(tmp_path,
                      "steps:\n  - task: UsePythonVersion@0\n    inputs:\n      versionSpec: '3.12'\n")
    block = yml.split("steps:")[1]
    assert block.index("uses:") < block.index("with:")


# --- full example ---

def test_full_example_kitchen_sink(tmp_path):
    report, yml = run_file(tmp_path, EXAMPLE.read_text())
    doc = yaml.safe_load(yml)
    jobs = doc["jobs"]
    assert list(jobs) == ["compile", "unit", "lint", "ship"]
    assert jobs["unit"]["needs"] == "compile"
    assert jobs["ship"]["needs"] == ["unit", "lint"]
    assert jobs["ship"]["if"] == "(success() && github.ref == 'refs/heads/main')"
    assert jobs["ship"]["timeout-minutes"] == 30
    assert jobs["lint"]["continue-on-error"] is True
    assert jobs["unit"]["strategy"]["max-parallel"] == 2
    # the multiline script must not have swallowed the sibling displayName key
    build_info = next(s for s in jobs["compile"]["steps"] if s.get("name") == "Build info")
    assert "splayName" not in build_info["run"]
    assert "$(git rev-parse HEAD)" in build_info["run"]
    assert "${{ github.sha }}" in build_info["run"]
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
    assert doc.get("on", doc.get(True))


def test_trigger_none_emits_no_push(tmp_path):
    _, yml = run_file(tmp_path, "trigger: none\nsteps:\n  - script: make\n")
    doc = yaml.safe_load(yml)
    on = doc.get("on", doc.get(True))
    assert "push" not in on
