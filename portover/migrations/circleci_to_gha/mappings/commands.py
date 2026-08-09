"""commands — reusable command definitions (inlined at each call site)."""

from portover.core import MappingMeta

SCOPE = "pipeline"

META = MappingMeta(
    id="commands",
    directive="commands: (reusable commands)",
    title="Migrate CircleCI reusable commands to GitHub Actions",
    before="""commands:
  install_deps:
    steps:
      - run: pip install -r requirements.txt

jobs:
  test:
    steps:
      - install_deps""",
    after="""jobs:
  test:
    steps:
      - run: pip install -r requirements.txt   # inlined from install_deps""",
    notes=(
        "GHA's equivalent is a composite action, which must live in its own "
        "directory with an action.yml — so portover inlines the command's steps "
        "at each call site instead, which is correct and keeps the workflow "
        "self-contained. If a command is called from many jobs and you'd rather "
        "share it, move those steps into .github/actions/<name>/action.yml and "
        "call it with `uses: ./.github/actions/<name>`. Command parameters "
        "(`<< parameters.x >>`) become matrix references when inlined — check "
        "them if the command took arguments."
    ),
    priority=14,
)

MAX_DEPTH = 5


def matches(key) -> bool:
    return key == "commands"


def apply(key, value, ctx, report) -> None:
    if not isinstance(value, dict):
        return
    for name, definition in value.items():
        ctx.commands[name] = definition if isinstance(definition, dict) else {}
        report.mapped(META.id, f"commands.{name}", "will be inlined at each call site")


def inline(name, args, ctx, report, *, depth: int = 0) -> list:
    """Expand a reusable command's steps at a call site."""
    from portover.migrations.circleci_to_gha import convert_steps

    if depth >= MAX_DEPTH:
        report.manual(META.id, f"step: {name}",
                      f"command nesting deeper than {MAX_DEPTH} — expand this one by hand")
        return []
    definition = ctx.commands.get(name) or {}
    values = {k: v.get("default") for k, v in (definition.get("parameters") or {}).items()
              if isinstance(v, dict) and "default" in v}
    if isinstance(args, dict):
        values.update(args)
    ctx.command_args.append(values)
    try:
        steps = convert_steps(definition.get("steps") or [], ctx, report, depth=depth + 1)
    finally:
        ctx.command_args.pop()
    declared = set(definition.get("parameters") or {})
    missing = declared - set(values)
    if missing:
        report.manual(META.id, f"step: {name}",
                      f"required command arguments missing: {sorted(missing)}")
    if isinstance(args, dict) and args:
        report.mapped(META.id, f"step: {name} with {sorted(args)}",
                      f"inlined {len(steps)} step(s) with arguments")
    else:
        report.mapped(META.id, f"step: {name}", f"inlined {len(steps)} step(s)")
    return steps
