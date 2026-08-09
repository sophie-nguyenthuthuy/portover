"""task — the Azure task catalog."""

from portover.core import MappingMeta

SCOPE = "step"

META = MappingMeta(
    id="task",
    directive="- task: Name@version",
    title="Migrate Azure Pipelines tasks to GitHub Actions",
    before="""- task: UsePythonVersion@0
  inputs:
    versionSpec: "3.12"
- task: PublishBuildArtifacts@1
  inputs:
    pathToPublish: dist
    artifactName: drop""",
    after="""- uses: actions/setup-python@v5
  with:
    python-version: "3.12"
- uses: actions/upload-artifact@v4
  with:
    name: drop
    path: dist""",
    notes=(
        "Tasks are Azure's equivalent of actions, and the common ones have "
        "direct counterparts — portover translates the setup, cache, artifact "
        "and shell tasks including their inputs. Tasks that only wrap a CLI "
        "(DotNetCoreCLI, NuGetCommand, CopyFiles, ArchiveFiles) become plain "
        "`run:` steps, which is usually clearer than hunting for an equivalent "
        "action. Azure-specific deployment tasks (AzureWebApp, AzureRmWebApp"
        "Deployment) map to the official azure/* actions but need "
        "azure/login and an OIDC or credentials secret first, so those are "
        "flagged rather than guessed. Anything unrecognised is flagged with "
        "the task name so you can search the marketplace."
    ),
    priority=12,
)

# task name (lowercased, no @version) -> (action, {azure input: gha with-key})
_ACTIONS = {
    "usepythonversion": ("actions/setup-python@v5", {"versionspec": "python-version",
                                                     "architecture": "architecture"}),
    "nodetool": ("actions/setup-node@v4", {"versionspec": "node-version"}),
    "usenode": ("actions/setup-node@v4", {"version": "node-version"}),
    "usedotnet": ("actions/setup-dotnet@v4", {"version": "dotnet-version"}),
    "dotnetcoreinstaller": ("actions/setup-dotnet@v4", {"version": "dotnet-version"}),
    "usejava": ("actions/setup-java@v4", {"version": "java-version"}),
    "javatoolinstaller": ("actions/setup-java@v4", {"versionspec": "java-version"}),
    "goTool": ("actions/setup-go@v5", {"version": "go-version"}),
    "useruby": ("ruby/setup-ruby@v1", {"versionspec": "ruby-version"}),
}

# tasks that become a plain shell command: name -> (input holding the command, shell)
_SHELL_TASKS = {
    "bash": ("script", "bash"),
    "cmdline": ("script", None),
    "powershell": ("script", "powershell"),
    "pwsh": ("script", "pwsh"),
    "shellscript": ("scriptpath", None),
}

_FLAGGED = {
    "azurewebapp": "use azure/webapps-deploy@v3 — it needs azure/login first (OIDC or a credentials secret)",
    "azurermwebappdeployment": "use azure/webapps-deploy@v3 after azure/login",
    "azurecli": "use azure/login@v2 then a plain `run:` step with the az CLI",
    "azurekeyvault": "use azure/login@v2 + azure/get-keyvault-secrets, or move the secrets into GitHub secrets",
    "docker": "use docker/build-push-action@v6 (with docker/login-action for the registry)",
    "dockercompose": "docker compose is available on the runner — call it from a `run:` step",
    "kubernetesmanifest": "use azure/k8s-deploy@v5, or kubectl from a `run:` step",
    "helmdeploy": "use azure/setup-helm@v4 then `helm upgrade` in a `run:` step",
    "sonarqubeprepare": "use SonarSource/sonarqube-scan-action",
    "npmauthenticate": "set the registry with actions/setup-node's registry-url + NODE_AUTH_TOKEN",
    "nugetauthenticate": "authenticate with a NuGet source and a token in a `run:` step",
    "publishcodecoverageresults": "no built-in coverage UI — use a coverage action or Codecov",
    "visualstudiotestplatform": "run vstest.console.exe from a `run:` step on a windows runner",
    "vstest": "run vstest.console.exe from a `run:` step on a windows runner",
    "msbuild": "use microsoft/setup-msbuild then call msbuild from a `run:` step",
    "vsbuild": "use microsoft/setup-msbuild then call msbuild from a `run:` step",
}


def matches(name) -> bool:
    return name == "task"


def apply(name, item, out, ctx, report) -> None:
    from portover.migrations.azure_pipelines_to_gha import rewrite_macros
    from portover.migrations.azure_pipelines_to_gha.expr import translate

    raw = str(item.get("task", ""))
    task = raw.split("@")[0]
    key = task.lower()
    inputs = {str(k).lower(): rewrite_macros(v, ctx, report)
              for k, v in (item.get("inputs") or {}).items()} \
        if isinstance(item.get("inputs"), dict) else {}

    step: dict = {}
    if item.get("displayName"):
        step["name"] = str(item["displayName"])
    if item.get("condition") is not None:
        condition = translate(item["condition"], report, META.id)
        if condition:
            step["if"] = condition
    if item.get("continueOnError"):
        step["continue-on-error"] = True

    handled = (_setup(key, inputs, step, ctx, report, raw)
               or _shell(key, inputs, item, step, ctx, report, raw)
               or _artifacts(key, inputs, step, ctx, report, raw)
               or _cache(key, inputs, step, ctx, report, raw)
               or _cli(key, inputs, step, ctx, report, raw))
    if not handled:
        hint = _FLAGGED.get(key, "no direct equivalent — search the GitHub Marketplace for this task")
        report.manual(META.id, f"task: {raw}", hint)
        step["run"] = f"echo 'TODO: port Azure task {raw} — {hint}'"
    out.append(step)


def _setup(key, inputs, step, ctx, report, raw) -> bool:
    entry = _ACTIONS.get(key)
    if not entry:
        return False
    action, input_map = entry
    with_: dict = {}
    for azure_key, gha_key in input_map.items():
        if azure_key in inputs:
            with_[gha_key] = str(inputs[azure_key]).strip()
    if action == "actions/setup-java@v4":
        with_.setdefault("distribution", "temurin")
    if with_:
        step["with"] = with_
    step["uses"] = action
    report.mapped(META.id, f"task: {raw}", action)
    return True


def _shell(key, inputs, item, step, ctx, report, raw) -> bool:
    from portover.migrations.azure_pipelines_to_gha import rewrite_macros

    entry = _SHELL_TASKS.get(key)
    if not entry:
        return False
    input_key, shell = entry
    command = inputs.get(input_key) or inputs.get("targettype") and inputs.get("script")
    step["run"] = rewrite_macros(str(command or ""), ctx, report)
    if shell:
        step["shell"] = shell
    if inputs.get("workingdirectory"):
        step["working-directory"] = str(inputs["workingdirectory"])
    report.mapped(META.id, f"task: {raw}", "run step")
    return True


def _artifacts(key, inputs, step, ctx, report, raw) -> bool:
    from portover.migrations.azure_pipelines_to_gha import rewrite_macros

    if key in ("publishbuildartifacts", "publishpipelineartifact"):
        path = inputs.get("pathtopublish") or inputs.get("targetpath") or "."
        name = inputs.get("artifactname") or inputs.get("artifact") or "drop"
        step["uses"] = "actions/upload-artifact@v4"
        step["with"] = {"name": str(name), "path": rewrite_macros(str(path), ctx, report)}
        report.mapped(META.id, f"task: {raw}", "actions/upload-artifact@v4")
        return True
    if key in ("downloadbuildartifacts", "downloadpipelineartifact", "download"):
        name = inputs.get("artifactname") or inputs.get("artifact")
        step["uses"] = "actions/download-artifact@v4"
        with_: dict = {}
        if name:
            with_["name"] = str(name)
        if inputs.get("downloadpath") or inputs.get("path"):
            with_["path"] = rewrite_macros(str(inputs.get("downloadpath") or inputs.get("path")), ctx, report)
        if with_:
            step["with"] = with_
        report.mapped(META.id, f"task: {raw}", "actions/download-artifact@v4")
        return True
    if key == "publishtestresults":
        files = inputs.get("testresultsfiles") or "**/test-*.xml"
        step["uses"] = "actions/upload-artifact@v4"
        step["if"] = step.get("if") or "always()"
        step["with"] = {"name": "test-results", "path": rewrite_macros(str(files), ctx, report)}
        report.manual(META.id, f"task: {raw}",
                      "uploaded as an artifact — GHA has no test-result UI; add dorny/test-reporter for annotations")
        return True
    return False


def _cache(key, inputs, step, ctx, report, raw) -> bool:
    from portover.migrations.azure_pipelines_to_gha import rewrite_macros

    if key != "cache":
        return False
    path = inputs.get("path") or ""
    key_input = str(inputs.get("key") or "")
    # Azure keys are | separated and may reference files with **/x
    parts = [p.strip() for p in key_input.split("|") if p.strip()]
    rendered = []
    for part in parts:
        if "**" in part or part.endswith((".lock", ".json", ".txt", ".toml")):
            rendered.append("${{ hashFiles('%s') }}" % part)
        elif part.lower() in ('"$(agent.os)"', "$(agent.os)"):
            rendered.append("${{ runner.os }}")
        else:
            rendered.append(rewrite_macros(part, ctx, report))
    step["uses"] = "actions/cache@v4"
    step["with"] = {"path": rewrite_macros(str(path), ctx, report),
                    "key": "-".join(rendered) or "${{ runner.os }}-cache"}
    if inputs.get("restorekeys"):
        step["with"]["restore-keys"] = str(inputs["restorekeys"])
    report.mapped(META.id, f"task: {raw}", "actions/cache@v4")
    return True


def _cli(key, inputs, step, ctx, report, raw) -> bool:
    """Tasks that are just a CLI call become a run step."""
    from portover.migrations.azure_pipelines_to_gha import rewrite_macros

    if key == "dotnetcorecli":
        command = str(inputs.get("command", "build"))
        args = str(inputs.get("arguments", ""))
        projects = str(inputs.get("projects", ""))
        step["run"] = " ".join(x for x in [f"dotnet {command}", projects, args] if x).strip()
    elif key == "nugetcommand":
        step["run"] = f"nuget {inputs.get('command', 'restore')} {inputs.get('arguments', '')}".strip()
    elif key == "copyfiles":
        source = inputs.get("sourcefolder", ".")
        target = inputs.get("targetfolder", ".")
        step["run"] = f"mkdir -p {target} && cp -r {source}/. {target}"
    elif key == "deletefiles":
        step["run"] = f"rm -rf {inputs.get('contents', '')}".strip()
    elif key == "archivefiles":
        root = inputs.get("rootfolderorfile", ".")
        archive = inputs.get("archivefile", "archive.zip")
        step["run"] = f"zip -r {archive} {root}"
    elif key == "extractfiles":
        step["run"] = f"unzip -o {inputs.get('archivefilepatterns', '*.zip')} -d {inputs.get('destinationfolder', '.')}"
    else:
        return False
    step["run"] = rewrite_macros(step["run"], ctx, report)
    report.mapped(META.id, f"task: {raw}", "run step (the task only wrapped a CLI)")
    return True
