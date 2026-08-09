"""clone / skip_clone / labels / platform / runs_on / variables."""

from portover.core import MappingMeta

SCOPE = "pipeline"

META = MappingMeta(
    id="workflow-settings",
    directive="clone / skip_clone / labels / platform / runs_on / variables",
    title="Migrate Woodpecker workflow settings to GitHub Actions",
    before="""labels:
  platform: linux/amd64

clone:
  git:
    image: woodpeckerci/plugin-git
    settings:
      depth: 50

runs_on: [success, failure]""",
    after="""runs-on: ubuntu-latest
steps:
  - uses: actions/checkout@v4
    with:
      fetch-depth: 50
# runs_on: [success, failure] -> if: always()""",
    notes=(
        "`labels:` selects an agent by tag; `platform: linux/amd64` maps to a "
        "GitHub-hosted runner, while other labels mean self-hosted runners "
        "carrying the same labels. The `clone:` block customises the built-in "
        "git step, and its `depth:` is `fetch-depth:` (`skip_clone: true` "
        "means no checkout at all). `runs_on:` is easy to misread — it is not "
        "runner selection but the set of upstream STATUSES this workflow runs "
        "for, so listing failure means `if: always()`. `variables:` is a "
        "holding area for YAML anchors, which portover's reader refuses rather "
        "than guessing at; expand them first."
    ),
    priority=12,
)

_PLATFORMS = {
    "linux/amd64": "ubuntu-latest", "linux": "ubuntu-latest",
    "windows/amd64": "windows-latest", "windows": "windows-latest",
    "darwin/amd64": "macos-latest", "darwin/arm64": "macos-latest", "darwin": "macos-latest",
}


def matches(key) -> bool:
    return key in ("clone", "skip_clone", "labels", "platform", "runs_on", "variables",
                   "environment", "workspace", "branches")


def apply(key, value, job, ctx, report) -> None:
    from portover.migrations.woodpecker_to_gha import as_env, as_list

    if key == "skip_clone":
        if value:
            job["_no_checkout"] = True
            report.mapped(META.id, "skip_clone: true", "no checkout step")
        return
    if key == "clone":
        _clone(value, job, report)
        return
    if key in ("labels", "platform"):
        _runner(key, value, job, report)
        return
    if key == "runs_on":
        statuses = {str(s) for s in as_list(value)}
        if "failure" in statuses:
            job["if"] = f"always() && ({job['if']})" if job.get("if") else "always()"
            report.mapped(META.id, f"runs_on: {sorted(statuses)}", "if: always()")
        else:
            report.mapped(META.id, f"runs_on: {sorted(statuses)}", "the GHA default")
        return
    if key == "environment":
        environment = as_env(value, ctx)
        if environment:
            job.setdefault("env", {}).update(environment)
            report.mapped(META.id, f"environment: {len(environment)} variable(s)", "job env")
        return
    if key == "branches":
        names = [str(b) for b in as_list(value.get("include") if isinstance(value, dict) else value)]
        if names:
            ctx.on.setdefault("push", {}).setdefault("branches", [])
            for name in names:
                if name not in ctx.on["push"]["branches"]:
                    ctx.on["push"]["branches"].append(name)
            report.mapped(META.id, f"branches: {names}", "on.push.branches")
        return
    if key == "workspace":
        report.mapped(META.id, f"workspace: {value}",
                      "dropped — GHA checks out into ${{ github.workspace }}")
        return
    if key == "variables":
        report.manual(META.id, "variables:",
                      "a holding area for YAML anchors — portover's reader does not expand "
                      "anchors, so inline them (or run `woodpecker-cli lint --expand`) first")


def _clone(value, job, report) -> None:
    if not isinstance(value, dict):
        return
    settings = {}
    for name, spec in value.items():
        if isinstance(spec, dict):
            settings.update(spec.get("settings") or {})
            if spec.get("image"):
                report.mapped("workflow-settings", f"clone.{name}.image", "dropped — actions/checkout replaces it")
    with_: dict = {}
    if settings.get("depth") is not None:
        with_["fetch-depth"] = int(settings["depth"])
        report.mapped("workflow-settings", f"clone depth: {settings['depth']}",
                      f"fetch-depth: {with_['fetch-depth']}")
    if settings.get("lfs"):
        with_["lfs"] = True
    if settings.get("recursive") or settings.get("submodules"):
        with_["submodules"] = "recursive"
    if with_:
        job["_checkout_with"] = with_


def _runner(key: str, value, job, report) -> None:
    tags = value if isinstance(value, dict) else {"platform": value}
    platform = str(tags.get("platform", "")).lower()
    runner = _PLATFORMS.get(platform)
    extra = [str(v) for k, v in tags.items() if k not in ("platform", "backend") and v]
    if runner and not extra:
        job["runs-on"] = runner
        report.mapped(META.id, f"{key}.platform: {platform}", f"runs-on: {runner}")
        return
    labels = ["self-hosted"] + ([platform] if platform else []) + extra
    job["runs-on"] = labels
    report.manual(META.id, f"{key}: {tags}",
                  f"agent labels — mapped to {labels}; register those agents as GitHub "
                  "self-hosted runners, or use a hosted runner if the labels only named an OS")
