"""script / bash / pwsh / powershell / checkout — the inline step forms."""

from portover.core import MappingMeta

SCOPE = "step"

META = MappingMeta(
    id="steps",
    directive="- script / bash / pwsh / powershell / checkout",
    title="Migrate Azure Pipelines script steps to GitHub Actions",
    before="""steps:
  - checkout: self
    fetchDepth: 0
  - script: pytest -q
    displayName: Run tests
    workingDirectory: backend
    env:
      TOKEN: $(SECRET_TOKEN)
  - bash: ./build.sh
    condition: succeeded()""",
    after="""steps:
  - uses: actions/checkout@v4
    with:
      fetch-depth: 0
  - name: Run tests
    run: pytest -q
    working-directory: backend
    env:
      TOKEN: ${{ env.SECRET_TOKEN }}
  - if: success()
    run: ./build.sh""",
    notes=(
        "`script:` is cmd on Windows agents and bash elsewhere; `bash:`, "
        "`pwsh:` and `powershell:` pin the shell and map to GHA's `shell:` key. "
        "The default differs per platform in both systems, so a `script:` step "
        "that relied on cmd syntax on a Windows agent needs `shell: cmd` "
        "adding. `checkout: self` is the repo (actions/checkout), "
        "`checkout: none` skips it — and note GHA does NOT check out "
        "automatically, so a job with no checkout step still gets one from "
        "portover unless the pipeline said `none`."
    ),
    priority=10,
)

_SHELLS = {"bash": "bash", "pwsh": "pwsh", "powershell": "powershell", "script": None}


def matches(name) -> bool:
    return name in ("script", "bash", "pwsh", "powershell", "checkout")


def convert(items, ctx, report) -> list:
    """Convert an Azure steps list, prepending checkout unless it opted out."""
    from portover.migrations.azure_pipelines_to_gha import as_list, scoped

    out: list = []
    explicit_checkout = False
    maps = scoped("step")
    for item in as_list(items):
        if isinstance(item, str):  # e.g. "- checkout: self" shorthand already dict; bare string is a script
            item = {"script": item}
        if not isinstance(item, dict):
            report.unmapped.append(f"step: {item!r}")
            continue
        name = _kind(item)
        if name == "checkout":
            explicit_checkout = True
        if name is None:
            report.unmapped.append(f"step: {sorted(item)}")
            continue
        for m in maps:
            if m.matches(name):
                m.apply(name, item, out, ctx, report)
                break
        else:
            report.unmapped.append(f"step: {name}")
    if not explicit_checkout:
        out.insert(0, {"uses": "actions/checkout@v4"})
    return out


def _kind(item: dict):
    for key in ("checkout", "task", "script", "bash", "pwsh", "powershell",
                "publish", "download", "template"):
        if key in item:
            return key
    return None


def apply(name, item, out, ctx, report) -> None:
    from portover.migrations.azure_pipelines_to_gha import rewrite_macros
    from portover.migrations.azure_pipelines_to_gha.expr import translate

    if name == "checkout":
        target = str(item.get("checkout"))
        if target == "none":
            report.mapped(META.id, "checkout: none", "no checkout step emitted")
            return
        step: dict = {"uses": "actions/checkout@v4"}
        with_: dict = {}
        if item.get("fetchDepth") is not None:
            with_["fetch-depth"] = int(item["fetchDepth"])
        if item.get("submodules"):
            with_["submodules"] = (True if str(item["submodules"]).lower() == "true"
                                   else str(item["submodules"]))
        if item.get("clean") is not None:
            report.mapped(META.id, f"checkout.clean: {item['clean']}",
                          "dropped — GHA jobs always start on a clean workspace")
        if item.get("persistCredentials"):
            with_["persist-credentials"] = True
        if with_:
            step["with"] = with_
        if target not in ("self", "none"):
            report.manual(META.id, f"checkout: {target}",
                          "checking out another repository — add `repository:` (and a token) to the checkout step")
        out.append(step)
        report.mapped(META.id, f"checkout: {target}", "actions/checkout@v4")
        return

    command = rewrite_macros(item.get(name), ctx, report)
    step = {}
    if item.get("displayName"):
        step["name"] = str(item["displayName"])
    if item.get("condition") is not None:
        condition = translate(item["condition"], report, META.id)
        if condition:
            step["if"] = condition
    step["run"] = command
    shell = _SHELLS.get(name)
    if shell:
        step["shell"] = shell
    if item.get("workingDirectory"):
        step["working-directory"] = rewrite_macros(str(item["workingDirectory"]), ctx, report)
    if isinstance(item.get("env"), dict):
        step["env"] = {k: rewrite_macros(v, ctx, report) for k, v in item["env"].items()}
    if item.get("continueOnError"):
        step["continue-on-error"] = True
    if item.get("timeoutInMinutes"):
        step["timeout-minutes"] = int(item["timeoutInMinutes"])
    if item.get("enabled") is False:
        report.manual(META.id, f"{name}: enabled: false",
                      "GHA has no disabled steps — delete it or gate it with `if: false`")
    out.append(step)
    report.mapped(META.id, f"{name} step")
