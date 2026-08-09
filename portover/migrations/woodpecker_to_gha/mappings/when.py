"""when — condition sets, at workflow or step level."""

from portover.core import MappingMeta

SCOPE = "pipeline"

META = MappingMeta(
    id="when",
    directive="when: [{event, branch, path, evaluate}]",
    title="Migrate Woodpecker when conditions to GitHub Actions if",
    before="""when:
  - event: push
    branch: main
  - event: tag""",
    after="if: (github.event_name == 'push' && github.ref_name == 'main') || github.ref_type == 'tag'",
    notes=(
        "This is the shape that differs most from Drone: Woodpecker's `when:` "
        "is a LIST of condition sets, and the sets are OR'd while the keys "
        "inside one set are AND'd — so the example runs on pushes to main and "
        "on any tag. portover reproduces that grouping exactly. (The single-map "
        "form is still accepted and behaves as one set.) `status: [success, "
        "failure]` becomes `always()` and is placed first, since a GHA step "
        "otherwise skips after a failure. `evaluate:` holds a CEL expression "
        "over Woodpecker's own variables and has no mechanical translation, so "
        "it is reported with its source text."
    ),
    priority=14,
)

_EVENTS = {
    "push": "github.event_name == 'push'",
    "pull_request": "github.event_name == 'pull_request'",
    "pull_request_closed": "github.event_name == 'pull_request'",
    "tag": "github.ref_type == 'tag'",
    "release": "github.event_name == 'release'",
    "deployment": "github.event_name == 'deployment'",
    "cron": "github.event_name == 'schedule'",
    "manual": "github.event_name == 'workflow_dispatch'",
}

# Woodpecker event -> the GHA trigger it needs in `on:`
TRIGGERS = {
    "push": ("push", {}),
    "pull_request": ("pull_request", {}),
    "pull_request_closed": ("pull_request", {}),
    "tag": ("push", {"tags": ["*"]}),
    "release": ("release", {}),
    "deployment": ("deployment", {}),
    "manual": ("workflow_dispatch", {}),
    "cron": ("schedule", None),
}


def matches(key) -> bool:
    return key == "when"


def apply(key, value, job, ctx, report) -> None:
    condition = build(value, ctx, report, triggers=True)
    if condition:
        job["if"] = f"{job['if']} && ({condition})" if job.get("if") else condition
        report.mapped(META.id, "when (workflow)", f"job if: {condition}")


def build(value, ctx, report, *, triggers: bool = False) -> str | None:
    """Render a when: block. Sets are OR'd; keys within a set are AND'd."""
    from portover.migrations.woodpecker_to_gha import as_list

    sets = value if isinstance(value, list) else [value]
    rendered_sets = []
    always = False
    for condition_set in sets:
        if not isinstance(condition_set, dict):
            continue
        parts, set_always = _one_set(condition_set, ctx, report, triggers=triggers)
        always = always or set_always
        if parts:
            rendered_sets.append(parts[0] if len(parts) == 1 else "(" + " && ".join(parts) + ")")

    conditions = []
    if always:
        conditions.append("always()")
    if rendered_sets:
        conditions.append(rendered_sets[0] if len(rendered_sets) == 1
                          else "(" + " || ".join(rendered_sets) + ")")
    return " && ".join(conditions) if conditions else None


def _one_set(condition_set: dict, ctx, report, *, triggers: bool):
    from portover.migrations.woodpecker_to_gha import as_list

    parts: list = []
    always = False
    for kind, spec in condition_set.items():
        includes = as_list(spec.get("include") if isinstance(spec, dict) else spec)
        excludes = as_list(spec.get("exclude") if isinstance(spec, dict) else None)

        if kind == "status":
            if "failure" in {str(s) for s in includes}:
                always = True
                report.mapped(META.id, f"when.status: {[str(s) for s in includes]}", "always()")
            continue
        if kind == "evaluate":
            report.manual(META.id, f"when.evaluate: {spec}",
                          "a CEL expression over Woodpecker variables — rewrite it as a GHA "
                          "expression by hand")
            continue
        if kind == "path":
            paths = [str(p) for p in includes] or [str(p) for p in excludes]
            report.manual(META.id, f"when.path: {paths}",
                          "GHA path filters are workflow-level (`on: push: paths:`) — for a "
                          "per-job or per-step filter use dorny/paths-filter")
            continue
        if kind in ("repo", "instance", "platform", "matrix", "cron", "environment"):
            report.manual(META.id, f"when.{kind}: {includes or excludes}",
                          f"`{kind}` has no GHA equivalent — drop it or express it as an env check")
            continue

        for value in includes:
            rendered = _condition(kind, value, ctx, report, triggers=triggers)
            if rendered:
                parts.append(rendered)
        for value in excludes:
            rendered = _condition(kind, value, ctx, report, triggers=False)
            if rendered:
                parts.append(f"!({rendered})")
    return parts, always


def _condition(kind: str, value, ctx, report, *, triggers: bool) -> str | None:
    text = str(value)
    if kind == "event":
        rendered = _EVENTS.get(text)
        if rendered is None:
            report.manual(META.id, f"when.event: {text}", "unrecognised Woodpecker event")
            return None
        if triggers:
            _add_trigger(text, ctx, report)
        report.mapped(META.id, f"when.event: {text}", rendered)
        return rendered
    if kind == "branch":
        rendered = (f"startsWith(github.ref_name, '{text.rstrip('*')}')" if text.endswith("*")
                    else f"github.ref_name == '{text}'")
        report.mapped(META.id, f"when.branch: {text}", rendered)
        return rendered
    if kind == "ref":
        return (f"startsWith(github.ref, '{text.rstrip('*')}')" if text.endswith("*")
                else f"github.ref == '{text}'")
    report.manual(META.id, f"when.{kind}: {text}", "no GHA equivalent for this condition type")
    return None


def _add_trigger(event: str, ctx, report) -> None:
    name, spec = TRIGGERS.get(event, (None, None))
    if name is None:
        return
    if spec is None:
        report.manual(META.id, "when.event: cron",
                      "the schedule lives in Woodpecker's UI, not this file — add "
                      "`on: schedule: - cron: ...` with the right expression")
        return
    if event == "push":
        ctx.plain_push = True
    existing = ctx.on.setdefault(name, {})
    for k, v in spec.items():
        existing.setdefault(k, v)
