"""when — step conditions."""

from portover.core import MappingMeta

SCOPE = "step"

META = MappingMeta(
    id="when",
    directive="when: branch / event / status / ref / path",
    title="Migrate Drone when conditions to GitHub Actions if",
    before="""when:
  branch:
    - main
  event:
    - push
  status:
    - success
    - failure""",
    after="if: always() && github.ref_name == 'main' && github.event_name == 'push'",
    notes=(
        "Each condition type becomes part of one `if:` expression. The one "
        "that changes meaning is `status:` — listing both success and failure "
        "is Drone's way of saying 'run even if an earlier step failed', which "
        "is `always()` in GHA (and must come FIRST in the expression, since a "
        "GHA step otherwise skips after a failure). `event:` values map onto "
        "event names, with `tag` becoming a ref-type check. The exclude form "
        "(`branch: {exclude: [main]}`) becomes a negation. `path:` filters have "
        "no per-step equivalent — GHA path filters are workflow-level — so "
        "those are flagged with the dorny/paths-filter alternative."
    ),
    priority=16,
)

_EVENTS = {
    "push": "github.event_name == 'push'",
    "pull_request": "github.event_name == 'pull_request'",
    "tag": "github.ref_type == 'tag'",
    "cron": "github.event_name == 'schedule'",
    "custom": "github.event_name == 'workflow_dispatch'",
    "promote": "github.event_name == 'workflow_dispatch'",
    "rollback": "github.event_name == 'workflow_dispatch'",
    "deployment": "github.event_name == 'deployment'",
}


def matches(key) -> bool:
    return key == "when"


def apply(key, value, step, ctx, report) -> None:
    condition = build(value, ctx, report)
    if condition:
        step["if"] = f"{step['if']} && {condition}" if step.get("if") else condition


def build(value, ctx, report) -> str | None:
    """Shared with the pipeline-level trigger mapping."""
    from portover.migrations.drone_to_gha import as_list

    if not isinstance(value, dict):
        return None
    parts: list = []
    always = False

    for kind, spec in value.items():
        includes = as_list(spec.get("include") if isinstance(spec, dict) else spec)
        excludes = as_list(spec.get("exclude") if isinstance(spec, dict) else None)

        if kind == "status":
            statuses = {str(s) for s in includes}
            if "failure" in statuses:
                always = True
                report.mapped(META.id, f"when.status: {sorted(statuses)}", "always()")
            continue
        if kind == "path":
            paths = [str(p) for p in includes] or [str(p) for p in excludes]
            report.manual(META.id, f"when.path: {paths}",
                          "GHA path filters are workflow-level — for a per-step filter use "
                          "dorny/paths-filter and gate on its output")
            continue
        if kind in ("instance", "cron", "matrix", "repo", "target"):
            report.manual(META.id, f"when.{kind}: {includes or excludes}",
                          f"`{kind}` has no GHA equivalent — drop it or express it as an env check")
            continue

        rendered_in = [c for c in (_condition(kind, v, report) for v in includes) if c]
        rendered_out = [c for c in (_condition(kind, v, report) for v in excludes) if c]
        if rendered_in:
            parts.append(rendered_in[0] if len(rendered_in) == 1
                         else "(" + " || ".join(rendered_in) + ")")
        for cond in rendered_out:
            parts.append(f"!({cond})")

    if always:
        parts.insert(0, "always()")
    return " && ".join(parts) if parts else None


def _condition(kind: str, value, report) -> str | None:
    text = str(value)
    if kind == "event":
        rendered = _EVENTS.get(text)
        if rendered is None:
            report.manual(META.id, f"when.event: {text}", "unrecognised Drone event")
        else:
            report.mapped(META.id, f"when.event: {text}", rendered)
        return rendered
    if kind == "branch":
        rendered = (f"startsWith(github.ref_name, '{text.rstrip('*')}')" if text.endswith("*")
                    else f"github.ref_name == '{text}'")
        report.mapped(META.id, f"when.branch: {text}", rendered)
        return rendered
    if kind == "ref":
        if text.endswith("*"):
            return f"startsWith(github.ref, '{text.rstrip('*')}')"
        return f"github.ref == '{text}'"
    report.manual(META.id, f"when.{kind}: {text}", "no GHA equivalent for this condition type")
    return None
