"""cache — pip/npm/yarn/directories."""

from portover.core import MappingMeta

META = MappingMeta(
    id="cache",
    directive="cache: pip / npm / directories",
    title="Migrate Travis cache to GitHub Actions",
    before="cache: pip",
    after="""- uses: actions/setup-python@v5
  with:
    python-version: "3.12"
    cache: pip""",
    notes=(
        "Package-manager caches are built into the setup-* actions (one line). "
        "cache: directories becomes actions/cache — pick a real key: portover "
        "uses a lockfile hash placeholder you must point at your actual "
        "dependency file."
    ),
    priority=18,  # after language, so the setup step exists to annotate
)

_BUILTIN = {"pip": "actions/setup-python", "npm": "actions/setup-node", "yarn": "actions/setup-node"}


def matches(key) -> bool:
    return key == "cache"


def _kinds(value):
    if isinstance(value, dict):
        return [k for k, v in value.items() if v or k == "directories"], value.get("directories") or []
    return [str(value)], []


def apply(key, value, ctx, report) -> None:
    kinds, directories = _kinds(value)
    for kind in kinds:
        if kind == "directories":
            continue
        action = _BUILTIN.get(kind)
        step = next((s for s in ctx.setup_steps if action and s.get("uses", "").startswith(action)), None)
        if step is not None:
            step.setdefault("with", {})["cache"] = kind if kind != "yarn" else "yarn"
            report.mapped(META.id, f"cache: {kind}", f"cache: {kind} on {step['uses']}")
        else:
            report.manual(META.id, f"cache: {kind}", f"no matching setup-* step to attach '{kind}' cache — add actions/cache")
    if directories:
        dirs = [str(d) for d in directories]
        ctx.pre_steps.append({"uses": "actions/cache@v4",
                              "with": {"path": "\n".join(dirs),
                                       "key": "${{ runner.os }}-cache-${{ hashFiles('**/lockfile') }}"}})
        report.manual(META.id, f"cache.directories: {dirs}",
                      "actions/cache added — replace the hashFiles('**/lockfile') key with your real dependency file")
