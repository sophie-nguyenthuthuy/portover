"""parameters — string/booleanParam/choice -> workflow_dispatch inputs."""

from portover.core import MappingMeta
from portover.migrations.jenkins_to_gha.parser import kwargs

SCOPE = "pipeline"

META = MappingMeta(
    id="parameters",
    directive="parameters { string / booleanParam / choice }",
    title="Migrate Jenkins parameters to workflow_dispatch inputs",
    before="parameters {\n  string(name: 'ENV', defaultValue: 'staging', description: 'target')\n  booleanParam(name: 'DRY_RUN', defaultValue: true)\n}",
    after="""on:
  workflow_dispatch:
    inputs:
      ENV:
        type: string
        default: staging
        description: target
      DRY_RUN:
        type: boolean
        default: true""",
    notes=(
        "Reference them as ${{ inputs.ENV }} instead of params.ENV. Unlike "
        "Jenkins, inputs only exist on manual runs — give push/schedule runs a "
        "fallback: ${{ inputs.ENV || 'staging' }}."
    ),
    priority=20,
)

_TYPES = {"string": "string", "text": "string", "booleanParam": "boolean", "choice": "choice", "password": None}


def matches(node) -> bool:
    return node.keyword() == "parameters"


def apply(node, ctx, report) -> None:
    inputs: dict = {}
    for stmt in node.stmts:
        kind = stmt.split("(")[0].strip()
        kw = kwargs(stmt)
        name = kw.get("name", "PARAM")
        if kind == "password" or kind not in _TYPES:
            report.manual(META.id, stmt, f"parameter type '{kind}' — use a repo secret or plain string input")
            continue
        inp: dict = {"type": _TYPES[kind]}
        if "defaultValue" in kw:
            dv = kw["defaultValue"]
            inp["default"] = dv.lower() == "true" if kind == "booleanParam" else dv
        if "description" in kw:
            inp["description"] = kw["description"]
        if kind == "choice":
            opts = kw.get("choices", "")
            inp["options"] = [o.strip(" '\"") for o in opts.strip("[]").split(",") if o.strip()]
        inputs[name] = inp
        report.mapped(META.id, stmt, f"inputs.{name} ({inp['type']})")
    if inputs:
        ctx.workflow["on"].setdefault("workflow_dispatch", {})["inputs"] = inputs
