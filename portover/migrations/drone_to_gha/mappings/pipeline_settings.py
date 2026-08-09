"""platform / clone / workspace / volumes / node / image_pull_secrets."""

from portover.core import MappingMeta

SCOPE = "pipeline"

META = MappingMeta(
    id="pipeline-settings",
    directive="platform / clone / workspace / volumes / node / image_pull_secrets",
    title="Migrate Drone pipeline settings to GitHub Actions",
    before="""platform:
  os: linux
  arch: amd64

clone:
  depth: 50

workspace:
  path: /drone/src""",
    after="""runs-on: ubuntu-latest
steps:
  - uses: actions/checkout@v4
    with:
      fetch-depth: 50""",
    notes=(
        "`platform` picks the runner: linux/amd64 is ubuntu-latest, "
        "windows is windows-latest, darwin is macos-latest, and arm64 needs a "
        "self-hosted or ARM runner. `clone.depth` maps to `fetch-depth` "
        "(`clone.disable: true` means no checkout at all). `workspace.path` "
        "has no equivalent worth reproducing — GHA always checks out into "
        "${{ github.workspace }}, and anything reading $DRONE_WORKSPACE should "
        "use that instead. `volumes`, `node` (agent labels) and "
        "`image_pull_secrets` describe the Drone runner fleet and are flagged."
    ),
    priority=12,
)

_PLATFORM = {("linux", "amd64"): "ubuntu-latest", ("linux", ""): "ubuntu-latest",
             ("windows", "amd64"): "windows-latest", ("windows", ""): "windows-latest",
             ("darwin", "amd64"): "macos-latest", ("darwin", "arm64"): "macos-latest",
             ("darwin", ""): "macos-latest"}


def matches(key) -> bool:
    return key in ("platform", "clone", "workspace", "volumes", "node",
                   "image_pull_secrets", "concurrency", "environment")


def apply(key, value, job, ctx, report) -> None:
    if key == "platform":
        os_name = str((value or {}).get("os", "linux")).lower() if isinstance(value, dict) else "linux"
        arch = str((value or {}).get("arch", "")).lower() if isinstance(value, dict) else ""
        runner = _PLATFORM.get((os_name, arch))
        if runner is None:
            job["runs-on"] = ["self-hosted", os_name, arch or "amd64"]
            report.manual(META.id, f"platform: {os_name}/{arch}",
                          "no GitHub-hosted runner for that platform — use a self-hosted or "
                          "ARM runner with these labels")
        else:
            job["runs-on"] = runner
            report.mapped(META.id, f"platform: {os_name}/{arch or 'amd64'}", f"runs-on: {runner}")
        return
    if key == "clone":
        if not isinstance(value, dict):
            return
        if value.get("disable"):
            job["_no_checkout"] = True
            report.mapped(META.id, "clone.disable: true", "no checkout step")
            return
        with_: dict = {}
        if value.get("depth") is not None:
            with_["fetch-depth"] = int(value["depth"])
            report.mapped(META.id, f"clone.depth: {value['depth']}", f"fetch-depth: {value['depth']}")
        if value.get("lfs"):
            with_["lfs"] = True
        if with_:
            job["_checkout_with"] = with_
        return
    if key == "workspace":
        report.mapped(META.id, f"workspace: {value}",
                      "dropped — GHA checks out into ${{ github.workspace }}")
        return
    if key == "environment":
        if isinstance(value, dict):
            from portover.migrations.drone_to_gha import secret_ref

            job["env"] = {str(k): secret_ref(v, ctx, report) for k, v in value.items()}
            report.mapped(META.id, f"environment: {len(value)} variable(s)", "job env")
        return
    if key == "concurrency":
        limit = value.get("limit") if isinstance(value, dict) else value
        job["concurrency"] = {"group": f"${{{{ github.workflow }}}}-{ctx.current_jid}",
                              "cancel-in-progress": False}
        report.mapped(META.id, f"concurrency.limit: {limit}",
                      "concurrency group — GHA serialises rather than capping at N")
        return
    if key == "volumes":
        report.manual(META.id, "pipeline volumes",
                      "host and temp volumes have no GHA equivalent — the workspace is already "
                      "shared between steps, and host paths do not exist on a hosted runner")
        return
    if key == "node":
        report.manual(META.id, f"node: {value}",
                      "agent selection labels — map them onto self-hosted runner labels")
        return
    if key == "image_pull_secrets":
        report.manual(META.id, f"image_pull_secrets: {value}",
                      "add docker/login-action@v3 (or container credentials) with the registry secret")
