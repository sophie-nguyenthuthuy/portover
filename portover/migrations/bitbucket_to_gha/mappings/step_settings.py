"""size / max-time / oidc / runs-on / fail-fast / condition — the smaller step fields."""

from portover.core import MappingMeta

SCOPE = "step"

META = MappingMeta(
    id="step-settings",
    directive="size / max-time / oidc / runs-on / fail-fast / condition",
    title="Migrate the remaining Bitbucket Pipelines step settings to GitHub Actions",
    before="""- step:
    size: 2x
    max-time: 30
    oidc: true
    runs-on: [self.hosted, linux]
    condition:
      changesets:
        includePaths: [src/**]""",
    after="""timeout-minutes: 30
permissions:
  id-token: write        # oidc: true
runs-on: [self-hosted, linux]
# condition.changesets -> dorny/paths-filter, or on: push: paths:""",
    notes=(
        "`max-time` is `timeout-minutes` (note the defaults differ: Bitbucket "
        "caps a step at 120 minutes, GHA at 360). `oidc: true` becomes "
        "`permissions: id-token: write`, which is the same mechanism for "
        "keyless cloud auth. `size` (2x/4x/8x) buys a bigger container and maps "
        "to a larger runner label your org configures. `condition.changesets` "
        "is a per-step path filter; GHA path filters are per-workflow, so the "
        "per-job equivalent is dorny/paths-filter."
    ),
    priority=26,
)


def matches(key) -> bool:
    return key in ("size", "max-time", "oidc", "runs-on", "fail-fast", "condition")


def apply(key, value, job, ctx, report) -> None:
    from portover.migrations.bitbucket_to_gha import as_list

    if key == "max-time":
        try:
            job["timeout-minutes"] = int(value)
            report.mapped(META.id, f"max-time: {value}", "timeout-minutes")
        except (TypeError, ValueError):
            report.manual(META.id, f"max-time: {value}", "could not parse — set timeout-minutes by hand")
        return
    if key == "oidc":
        if value:
            job.setdefault("permissions", {})["id-token"] = "write"
            job["permissions"].setdefault("contents", "read")
            report.mapped(META.id, "oidc: true", "permissions.id-token: write")
        return
    if key == "size":
        report.manual(META.id, f"size: {value}",
                      "a bigger container — use a larger GitHub-hosted runner label "
                      "(configured by your org) or a self-hosted runner")
        return
    if key == "runs-on":
        labels = [str(t).replace("self.hosted", "self-hosted") for t in as_list(value)]
        if "self-hosted" not in labels:
            labels = ["self-hosted", *labels]
        job["runs-on"] = labels
        report.manual(META.id, f"runs-on: {as_list(value)}",
                      "Bitbucket runner labels — register those machines as GitHub self-hosted runners")
        return
    if key == "fail-fast":
        report.mapped(META.id, f"fail-fast: {value}", "handled by the parallel mapping")
        return
    if key == "condition":
        paths = []
        if isinstance(value, dict):
            changesets = value.get("changesets")
            if isinstance(changesets, dict):
                paths = [str(p) for p in as_list(changesets.get("includePaths"))]
        report.manual(META.id, f"condition.changesets: {paths}",
                      "GHA path filters are per-workflow (`on: push: paths:`) — for a per-job "
                      "filter use dorny/paths-filter and gate the job on its output")
