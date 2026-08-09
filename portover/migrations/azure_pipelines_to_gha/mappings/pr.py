"""pr — pull request triggers."""

from portover.core import MappingMeta

SCOPE = "pipeline"

META = MappingMeta(
    id="pr",
    directive="pr: branches / paths / drafts / none",
    title="Migrate Azure Pipelines pr triggers to GitHub Actions",
    before="""pr:
  branches:
    include: [main]
  drafts: false""",
    after="""on:
  pull_request:
    branches: [main]
    # drafts: filter with
    # if: github.event.pull_request.draft == false""",
    notes=(
        "`pr.branches` filters the TARGET branch, same as GHA's "
        "`pull_request.branches` — a common misreading is to think it filters "
        "the source branch. `drafts: false` has no trigger-level equivalent: "
        "GHA runs on draft PRs, so add "
        "`if: github.event.pull_request.draft == false` to the jobs. "
        "`pr: none` disables PR validation entirely."
    ),
    priority=12,
)


def matches(key) -> bool:
    return key == "pr"


def apply(key, value, ctx, report) -> None:
    from portover.migrations.azure_pipelines_to_gha import as_list

    if value is None or str(value).lower() == "none":
        ctx.on.pop("pull_request", None)
        report.mapped(META.id, "pr: none", "no pull_request trigger emitted")
        return
    spec: dict = {}
    if isinstance(value, list):
        spec["branches"] = [str(b) for b in value]
    elif isinstance(value, dict):
        if value.get("drafts") is False:
            report.manual(META.id, "pr.drafts: false",
                          "GHA runs on draft PRs — add `if: github.event.pull_request.draft == false` to the jobs")
        for section, (inc_key, exc_key) in (("branches", ("branches", "branches-ignore")),
                                            ("paths", ("paths", "paths-ignore"))):
            sub = value.get(section)
            if sub is None:
                continue
            includes = [str(v) for v in as_list(sub.get("include") if isinstance(sub, dict) else sub)]
            excludes = [str(v) for v in as_list(sub.get("exclude") if isinstance(sub, dict) else None)]
            if includes:
                spec[inc_key] = includes
            elif excludes:
                spec[exc_key] = excludes
    ctx.on["pull_request"] = spec
    report.mapped(META.id, "pr", f"on.pull_request {sorted(spec) or '(all)'}")
