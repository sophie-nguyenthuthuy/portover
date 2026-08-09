"""pipelines — the trigger sections and the step sequence inside each."""

from portover.core import MappingMeta
from portover.emit import yaml_dump

SCOPE = "pipeline"

META = MappingMeta(
    id="pipelines",
    directive="pipelines: default / branches / tags / pull-requests / custom",
    title="Migrate Bitbucket Pipelines sections to GitHub Actions workflows",
    before="""pipelines:
  default:
    - step:
        name: Build
        script: [make build]
    - step:
        name: Test
        script: [make test]
  branches:
    main:
      - step:
          script: [./deploy.sh]""",
    after="""# .github/workflows/default.yml
on: {push: {}}
jobs:
  build:
    steps: [...]
  test:
    needs: build      # steps are sequential in Bitbucket
    steps: [...]

# .github/workflows/branches-main.yml
on: {push: {branches: [main]}}""",
    notes=(
        "Each section is triggered differently, and GHA scopes triggers per "
        "FILE, so each becomes its own workflow. `default` is every push that "
        "no `branches:` pattern claims — GHA has no 'everything else' trigger, "
        "so portover emits a plain `on: push` and flags it when specific "
        "branch pipelines exist alongside it. `custom:` pipelines are manual, "
        "which is `workflow_dispatch` (their `variables:` become inputs). "
        "Within a section, steps run one after another, so they are chained "
        "with `needs:` — and because Bitbucket hands each step the artifacts "
        "of every earlier step automatically, portover inserts the matching "
        "download-artifact steps that GHA requires."
    ),
    priority=40,
)

_SECTIONS = ("default", "branches", "tags", "pull-requests", "custom", "bookmarks")


def matches(key) -> bool:
    return key == "pipelines"


def apply(key, value, ctx, report) -> None:
    if not isinstance(value, dict):
        return
    has_branches = bool(value.get("branches"))
    for section, spec in value.items():
        if section not in _SECTIONS:
            report.unmapped.append(f"pipelines.{section}")
            continue
        if section == "bookmarks":
            report.manual(META.id, "pipelines.bookmarks",
                          "Mercurial bookmarks — no Git/GHA equivalent")
            continue
        if section == "default":
            _emit("default", spec, {"push": {}}, ctx, report,
                  note=("`default` runs on any push not claimed by a branches: pattern — "
                        "GHA has no fallback trigger, so exclude those branches with branches-ignore")
                  if has_branches else None)
            continue
        if not isinstance(spec, dict):
            continue
        for pattern, steps in spec.items():
            _emit_pattern(section, str(pattern), steps, ctx, report)


def _emit_pattern(section: str, pattern: str, steps, ctx, report) -> None:
    from portover.migrations.bitbucket_to_gha import slug

    if section == "branches":
        on = {"push": {"branches": [pattern]}}
    elif section == "tags":
        on = {"push": {"tags": [pattern]}}
    elif section == "pull-requests":
        on = {"pull_request": {} if pattern in ("**", "*") else {"branches": [pattern]}}
        if pattern not in ("**", "*"):
            report.manual(META.id, f"pull-requests.{pattern}",
                          "a pull-requests pattern matches the SOURCE branch in Bitbucket, but "
                          "`pull_request.branches` filters the TARGET — check this one")
    else:  # custom
        on = {"workflow_dispatch": {}}
        inputs = _custom_inputs(steps, report, pattern)
        if inputs:
            on["workflow_dispatch"] = {"inputs": inputs}
        steps = _custom_steps(steps)
        # Bitbucket passes custom variables to scripts as environment variables;
        # keep `$version` working by defining it from the dispatch input.
        _emit(f"custom-{slug(pattern)}", steps, on, ctx, report,
              extra_env={name: "${{ inputs.%s }}" % name for name in inputs})
        return
    name = section if pattern in ("**", "*") else f"{section}-{slug(pattern)}"
    _emit(name, steps, on, ctx, report)


def _custom_inputs(steps, report, pattern) -> dict:
    """A custom pipeline may start with a `variables:` block of prompts."""
    from portover.migrations.bitbucket_to_gha import as_list

    inputs: dict = {}
    for entry in as_list(steps):
        if isinstance(entry, dict) and "variables" in entry:
            for variable in as_list(entry["variables"]):
                if not isinstance(variable, dict) or not variable.get("name"):
                    continue
                name = str(variable["name"])
                spec: dict = {"type": "string"}
                if variable.get("default") is not None:
                    spec["default"] = variable["default"]
                if variable.get("allowed-values"):
                    spec["type"] = "choice"
                    spec["options"] = [str(v) for v in as_list(variable["allowed-values"])]
                if variable.get("description"):
                    spec["description"] = str(variable["description"])
                inputs[name] = spec
                report.mapped(META.id, f"custom.{pattern} variable {name}", f"inputs.{name}")
    return inputs


def _custom_steps(steps):
    from portover.migrations.bitbucket_to_gha import as_list

    return [s for s in as_list(steps) if not (isinstance(s, dict) and "variables" in s)]


def _emit(workflow_name: str, steps, on: dict, ctx, report, *, note=None, extra_env=None) -> None:
    from portover.migrations.bitbucket_to_gha import as_list, build_step, order_job, slug
    from portover.migrations.bitbucket_to_gha.mappings import parallel as parallel_map
    from portover.migrations.bitbucket_to_gha.mappings import variables as variables_map

    ctx.used_vars = set()  # per-workflow: each file defines only what its own scripts use
    jobs: dict = {}
    taken: set = set()
    previous: list = []
    produced: list = []  # artifact names from earlier steps (Bitbucket passes them on)
    index = 1

    for entry in as_list(steps):
        if not isinstance(entry, dict):
            continue
        if "parallel" in entry:
            group, index = parallel_map.expand(entry["parallel"], ctx, report,
                                               index=index, taken=taken)
            current = []
            for jid, job in group:
                _wire(job, previous, produced)
                jobs[jid] = job
                current.append(jid)
                produced.extend(job.pop("_artifacts", []))
            previous = current
            continue
        if "stage" in entry:
            stage = entry["stage"] if isinstance(entry["stage"], dict) else {}
            report.mapped(META.id, f"stage: {stage.get('name', '?')}",
                          "stages are flattened — their steps keep the needs: chain")
            if stage.get("deployment"):
                report.manual(META.id, f"stage deployment: {stage['deployment']}",
                              "set `environment:` on each job of this stage")
            for sub in as_list(stage.get("steps")):
                if isinstance(sub, dict) and "step" in sub:
                    jid, job = build_step(sub["step"] or {}, ctx, report, index=index, taken=taken)
                    _wire(job, previous, produced)
                    jobs[jid] = job
                    produced.extend(job.pop("_artifacts", []))
                    previous = [jid]
                    index += 1
            continue
        if "step" not in entry:
            report.unmapped.append(f"pipeline entry: {sorted(entry)}")
            continue
        jid, job = build_step(entry["step"] or {}, ctx, report, index=index, taken=taken)
        _wire(job, previous, produced)
        jobs[jid] = job
        produced.extend(job.pop("_artifacts", []))
        previous = [jid]
        index += 1

    if not jobs:
        return
    doc: dict = {"name": workflow_name, "on": on}
    env = dict(extra_env or {})
    env.update(variables_map.compat_env(ctx, report))
    if env:
        doc["env"] = env
    doc["jobs"] = {j: order_job(job) for j, job in jobs.items()}
    path = f".github/workflows/{slug(workflow_name)}.yml"
    report.outputs[path] = yaml_dump(doc) + "\n"
    report.mapped(META.id, f"pipelines.{workflow_name}", f"{len(jobs)} job(s) -> {path}")
    if note:
        report.manual(META.id, f"pipelines.{workflow_name}", note)


def _wire(job: dict, previous: list, produced: list) -> None:
    """Chain onto the previous step and restore Bitbucket's artifact pass-through."""
    if previous:
        job["needs"] = previous if len(previous) > 1 else previous[0]
    if job.pop("_no_download", False) or not produced:
        return
    downloads = [{"uses": "actions/download-artifact@v4", "with": {"name": name}}
                 for name in dict.fromkeys(produced)]
    # steps are already assembled by build_step, so splice in just after checkout
    steps = job.setdefault("steps", [])
    at = 1 if steps and steps[0].get("uses", "").startswith("actions/checkout") else 0
    steps[at:at] = downloads
