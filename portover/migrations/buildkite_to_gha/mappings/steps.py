"""steps — the pipeline's step list."""

from portover.core import MappingMeta

SCOPE = "pipeline"

META = MappingMeta(
    id="steps",
    directive="steps: [command / wait / block / input / trigger / group]",
    title="Migrate Buildkite steps to GitHub Actions jobs",
    before="""steps:
  - label: Build
    key: build
    command: make build
  - wait
  - label: Test
    command: make test""",
    after="""jobs:
  build:
    name: Build
    steps:
      - uses: actions/checkout@v4
      - run: make build
  test:
    needs: build      # the wait barrier
    name: Test
    steps:
      - uses: actions/checkout@v4
      - run: make test""",
    notes=(
        "Buildkite and GHA already agree that work runs concurrently by "
        "default, so most steps become jobs with no `needs:` at all. The "
        "ordering comes from `wait` barriers and `depends_on`, which the wait "
        "and depends_on pages cover. A Buildkite step is a whole job, not a "
        "GHA step: it gets its own agent and its own checkout, so its "
        "`command:` list becomes that job's `run:` steps. Step `key:`s become "
        "the GHA job ids (that is what `depends_on` references); a step with "
        "only a label gets a slugged id, and emoji-prefixed labels like "
        "':docker: Build' keep the readable text as the job `name:`."
    ),
    priority=40,
)

_TYPES = ("command", "commands", "wait", "waiter", "block", "input", "trigger", "group")


def matches(key) -> bool:
    return key == "steps"


def apply(key, value, ctx, report) -> None:
    walk(value, ctx, report)


def walk(value, ctx, report, *, group_needs=None) -> None:
    from portover.migrations.buildkite_to_gha import as_list, build_command_step
    from portover.migrations.buildkite_to_gha.mappings import block_input, group as group_map
    from portover.migrations.buildkite_to_gha.mappings import trigger as trigger_map
    from portover.migrations.buildkite_to_gha.mappings import wait as wait_map

    index = len(ctx.job_order) + 1
    for entry in as_list(value):
        if entry is None:
            continue
        if isinstance(entry, str):
            if entry in ("wait", "waiter"):
                wait_map.barrier(None, ctx, report)
            else:  # bare string is shorthand for a command
                entry = {"command": entry}
            if isinstance(entry, str):
                continue
        if not isinstance(entry, dict):
            report.unmapped.append(f"step: {entry!r}")
            continue

        if "wait" in entry:
            wait_map.barrier(entry.get("wait"), ctx, report)
            continue
        if "group" in entry:
            group_map.expand(entry, ctx, report)
            index = len(ctx.job_order) + 1
            continue
        if "block" in entry or "input" in entry:
            jid, job = block_input.build(entry, ctx, report, index=index)
        elif "trigger" in entry:
            jid, job = trigger_map.build(entry, ctx, report, index=index)
        elif "command" in entry or "commands" in entry or "plugins" in entry:
            jid, job = build_command_step(entry, ctx, report, index=index)
        else:
            report.unmapped.append(f"step: {sorted(entry)}")
            continue

        _register(jid, job, entry, ctx, group_needs=group_needs)
        index += 1


def _register(jid, job, entry, ctx, *, group_needs=None) -> None:
    """Attach barrier/group ordering unless the step declared its own depends_on."""
    if "_explicit_needs" in job:
        job.pop("_explicit_needs")
    else:
        inherited = list(ctx.pending_needs)
        if group_needs:
            inherited = list(dict.fromkeys(inherited + list(group_needs)))
        if inherited:
            job["needs"] = inherited if len(inherited) > 1 else inherited[0]
    if entry.get("key"):
        ctx.keys[str(entry["key"])] = jid
    ctx.jobs[jid] = job
    ctx.job_order.append(jid)
    ctx.barrier.append(jid)
