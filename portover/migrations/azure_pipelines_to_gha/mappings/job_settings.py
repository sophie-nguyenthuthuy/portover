"""container / services / timeoutInMinutes / continueOnError / pool / workspace."""

from portover.core import MappingMeta

SCOPE = "job"

META = MappingMeta(
    id="job-settings",
    directive="container / services / timeoutInMinutes / continueOnError / workspace",
    title="Migrate Azure Pipelines job settings to GitHub Actions",
    before="""container: python:3.12
services:
  db: postgres
timeoutInMinutes: 30
continueOnError: true
workspace:
  clean: all""",
    after="""container: python:3.12
services:
  db:
    image: postgres
timeout-minutes: 30
continue-on-error: true
# workspace.clean: dropped — GHA jobs always start clean""",
    notes=(
        "Mostly direct renames. Two notes: the default timeout differs sharply "
        "(Azure gives Microsoft-hosted jobs 60 minutes, GHA gives 360), so a "
        "job that relied on Azure's default to kill a hang now runs six times "
        "longer — set it explicitly if it mattered. And `workspace: clean:` is "
        "unnecessary: every GHA job starts on a fresh runner, which is why "
        "`clean: all` has nothing to do."
    ),
    priority=26,
)


def matches(key) -> bool:
    return key in ("container", "services", "timeoutInMinutes", "continueOnError",
                   "pool", "workspace", "cancelTimeoutInMinutes", "uses")


def apply(key, value, job, ctx, report) -> None:
    from portover.migrations.azure_pipelines_to_gha.mappings import pool as pool_map

    if key == "pool":
        pool_map.resolve(value, job, ctx, report)
        return
    if key == "container":
        image = value.get("image") if isinstance(value, dict) else value
        if isinstance(value, dict) and value.get("endpoint"):
            report.manual(META.id, "container.endpoint",
                          "private registry — add docker/login-action, or `credentials:` under the container")
        job["container"] = str(image)
        report.mapped(META.id, f"container: {image}")
        return
    if key == "services":
        if not isinstance(value, dict):
            return
        for alias, spec in value.items():
            image = spec.get("image") if isinstance(spec, dict) else spec
            job.setdefault("services", {})[str(alias)] = {"image": str(image)}
            report.mapped(META.id, f"services.{alias}: {image}")
        return
    if key == "timeoutInMinutes":
        job["timeout-minutes"] = int(value)
        report.mapped(META.id, f"timeoutInMinutes: {value}", "timeout-minutes")
        return
    if key == "continueOnError":
        job["continue-on-error"] = bool(value)
        report.mapped(META.id, f"continueOnError: {value}", "continue-on-error")
        return
    if key == "workspace":
        report.mapped(META.id, f"workspace: {value}", "dropped — GHA jobs always start on a clean runner")
        return
    if key == "cancelTimeoutInMinutes":
        report.manual(META.id, f"cancelTimeoutInMinutes: {value}",
                      "no grace period for cancellation in GHA")
        return
    if key == "uses":  # job-level resource declaration (repositories/pools)
        report.manual(META.id, "uses: (job resources)",
                      "declare extra repositories with a second actions/checkout step")
