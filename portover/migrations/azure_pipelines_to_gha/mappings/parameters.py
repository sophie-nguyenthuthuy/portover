"""parameters — runtime parameters."""

from portover.core import MappingMeta

SCOPE = "pipeline"

META = MappingMeta(
    id="parameters",
    directive="parameters: [{name, type, default, values}]",
    title="Migrate Azure Pipelines parameters to workflow_dispatch inputs",
    before="""parameters:
  - name: deployEnv
    type: string
    default: staging
    values: [staging, production]
  - name: runSlowTests
    type: boolean
    default: false""",
    after="""on:
  workflow_dispatch:
    inputs:
      deployEnv:
        type: choice
        default: staging
        options: [staging, production]
      runSlowTests:
        type: boolean
        default: false""",
    notes=(
        "Both are run-time prompts, so this maps cleanly — a parameter with "
        "`values:` becomes a `choice` input with `options:`. The deeper "
        "difference is WHEN they are evaluated: Azure parameters are "
        "compile-time (`${{ parameters.x }}` can add or remove whole jobs "
        "before the run starts), while GHA inputs are run-time values only. A "
        "parameter used to conditionally include jobs therefore becomes an "
        "`if:` on those jobs, not a template expansion. Also note inputs exist "
        "only on manual runs — give push/schedule runs a fallback like "
        "`${{ inputs.deployEnv || 'staging' }}`."
    ),
    priority=18,
)

_TYPES = {"string": "string", "boolean": "boolean", "number": "number",
          "object": "string", "step": None, "stepList": None, "job": None, "jobList": None}


def matches(key) -> bool:
    return key == "parameters"


def apply(key, value, ctx, report) -> None:
    from portover.migrations.azure_pipelines_to_gha import as_list

    entries = ([{"name": k, **(v if isinstance(v, dict) else {"default": v})}
                for k, v in value.items()] if isinstance(value, dict) else as_list(value))
    for entry in entries:
        if not isinstance(entry, dict) or not entry.get("name"):
            continue
        name = str(entry["name"])
        kind = _TYPES.get(str(entry.get("type", "string")), "string")
        if kind is None:
            report.manual(META.id, f"parameters.{name} (type {entry.get('type')})",
                          "step/job list parameters are compile-time template plumbing — "
                          "restructure as a reusable workflow or an `if:` on the job")
            continue
        inp: dict = {"type": kind}
        if entry.get("values"):
            inp["type"] = "choice"
            inp["options"] = [str(v) for v in as_list(entry["values"])]
        if "default" in entry:
            inp["default"] = entry["default"]
        if entry.get("displayName"):
            inp["description"] = str(entry["displayName"])
        ctx.inputs[name] = inp
        ctx.declared.add(name)
        report.mapped(META.id, f"parameters.{name}", f"inputs.{name} ({inp['type']})")
