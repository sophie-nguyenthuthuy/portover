"""parameters — pipeline parameters."""

from portover.core import MappingMeta

SCOPE = "pipeline"

META = MappingMeta(
    id="parameters",
    directive="parameters: (pipeline parameters)",
    title="Migrate CircleCI pipeline parameters to workflow_dispatch inputs",
    before="""parameters:
  deploy_env:
    type: string
    default: staging
  run_slow_tests:
    type: boolean
    default: false""",
    after="""on:
  workflow_dispatch:
    inputs:
      deploy_env:
        type: string
        default: staging
      run_slow_tests:
        type: boolean
        default: false""",
    notes=(
        "References change from `<< pipeline.parameters.deploy_env >>` to "
        "`${{ inputs.deploy_env }}` — portover rewrites those tokens inside run "
        "commands for you. Note the trigger difference: CircleCI parameters can "
        "be set by API-triggered pipelines, while workflow_dispatch inputs only "
        "exist on manual runs, so give push/schedule runs a fallback like "
        "`${{ inputs.deploy_env || 'staging' }}`."
    ),
    priority=10,
)

_TYPES = {"string": "string", "boolean": "boolean", "integer": "number", "enum": "choice"}


def matches(key) -> bool:
    return key == "parameters"


def apply(key, value, ctx, report) -> None:
    if not isinstance(value, dict):
        return
    for name, spec in value.items():
        spec = spec if isinstance(spec, dict) else {}
        kind = _TYPES.get(str(spec.get("type", "string")), "string")
        inp = {"type": kind}
        if "default" in spec:
            inp["default"] = spec["default"]
        if spec.get("description"):
            inp["description"] = spec["description"]
        if kind == "choice" and spec.get("enum"):
            inp["options"] = [str(e) for e in spec["enum"]]
        ctx.inputs[name] = inp
        report.mapped(META.id, f"parameters.{name}", f"inputs.{name} ({kind})")
