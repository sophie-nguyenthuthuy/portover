"""needs — the job DAG."""

from portover.core import MappingMeta

SCOPE = "job"

META = MappingMeta(
    id="needs",
    directive="needs: [job] / needs: [{job, artifacts, optional}]",
    title="Migrate GitLab CI needs to GitHub Actions",
    before="""needs:
  - build
  - job: lint
    artifacts: false""",
    after="""needs: [build, lint]""",
    notes=(
        "The one GitLab directive that maps to GHA exactly — both are a job "
        "DAG, and declaring `needs:` overrides the stage order in both systems. "
        "Two details do not carry: `artifacts: false` (GHA never passes "
        "artifacts implicitly, so the flag is meaningless — you download what "
        "you want), and `optional: true` (GHA has no optional dependency; the "
        "job simply cannot depend on something that might not exist). "
        "`needs: []` means 'start immediately' in both."
    ),
    priority=24,
)


def matches(key) -> bool:
    return key == "needs"


def apply(key, value, job, ctx, report) -> None:
    from portover.migrations.gitlab_ci_to_gha import as_list, slug

    entries = as_list(value)
    names = []
    for entry in entries:
        if isinstance(entry, dict):
            name = entry.get("job")
            if entry.get("optional"):
                report.manual(META.id, f"needs.{name} optional: true",
                              "GHA has no optional dependency — drop it or always define the job")
            if entry.get("pipeline") or entry.get("project"):
                report.manual(META.id, f"needs.{name} cross-pipeline",
                              "cross-project needs have no equivalent — trigger via workflow_call or repository_dispatch")
                continue
        else:
            name = entry
        if name is not None:
            names.append(slug(str(name)))

    if names:
        job["needs"] = names if len(names) > 1 else names[0]
        report.mapped(META.id, f"needs: {names}")
    else:
        report.mapped(META.id, "needs: []", "no dependencies — job starts immediately")
    # mark the job so stage wiring does not overwrite an explicit DAG
    ctx.explicit_needs.add(ctx.current_jid)
