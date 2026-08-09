"""variables — pipeline and job variables."""

from portover.core import MappingMeta

SCOPE = "job"

META = MappingMeta(
    id="variables",
    directive="variables: (mapping, list, group or template)",
    title="Migrate Azure Pipelines variables to GitHub Actions env",
    before="""variables:
  appEnv: production
  - group: prod-secrets
  - name: buildConfig
    value: Release""",
    after="""env:
  appEnv: production
  buildConfig: Release
  # variable group 'prod-secrets' -> repository secrets or an Environment""",
    notes=(
        "All three spellings — a plain mapping, a list of name/value pairs, and "
        "the `${{ }}` template form — become `env:`. The one that cannot be "
        "translated is `- group:`: a variable group lives in Azure Library, not "
        "in the YAML, so portover cannot see its contents. Recreate those as "
        "repository or Environment secrets. Secret variables are the same "
        "story: they are never in the file, so nothing is silently carried over "
        "in plaintext."
    ),
    priority=24,
)


def matches(key) -> bool:
    return key == "variables"


def apply(key, value, job, ctx, report) -> None:
    target = job.setdefault("env", {}) if job is not None else ctx.variables
    _collect(value, target, ctx, report)


def apply_pipeline(value, ctx, report) -> None:
    _collect(value, ctx.variables, ctx, report)


def _collect(value, target: dict, ctx, report) -> None:
    from portover.migrations.azure_pipelines_to_gha import as_list, rewrite_macros

    if isinstance(value, dict):
        for name, spec in value.items():
            target[str(name)] = rewrite_macros(spec, ctx, report) if isinstance(spec, str) else spec
            ctx.declared.add(str(name))
            report.mapped(META.id, f"variables.{name}")
        return
    for entry in as_list(value):
        if not isinstance(entry, dict):
            continue
        if entry.get("group"):
            report.manual(META.id, f"variables group: {entry['group']}",
                          "variable groups live in Azure Library, not the YAML — recreate them as "
                          "repository secrets (or an Environment's secrets)")
            continue
        if entry.get("template"):
            report.manual(META.id, f"variables template: {entry['template']}",
                          "variable template — inline those values or move them into repo/Environment variables")
            continue
        name = entry.get("name")
        if name is None:
            continue
        spec = entry.get("value")
        target[str(name)] = rewrite_macros(spec, ctx, report) if isinstance(spec, str) else spec
        ctx.declared.add(str(name))
        report.mapped(META.id, f"variables.{name}")
