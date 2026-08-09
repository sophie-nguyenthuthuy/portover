"""when (step level) — per-step conditions."""

from portover.core import MappingMeta
from portover.migrations.woodpecker_to_gha.mappings import when as when_map

SCOPE = "step"

META = MappingMeta(
    id="step-when",
    directive="when: (on a step)",
    title="Migrate Woodpecker per-step when conditions to GitHub Actions",
    before="""- name: notify
  image: alpine
  when:
    - status: [success, failure]
  commands: [./notify.sh]""",
    after="""- name: notify
  if: always()
  run: ./notify.sh""",
    notes=(
        "The same condition-set grammar as a workflow-level `when:`, applied "
        "to one step. The difference in effect is worth noting: a step "
        "condition becomes an `if:` on a GHA STEP, and unlike the workflow "
        "level it cannot add triggers — a step cannot make the workflow run "
        "for an event the workflow was not triggered for. So a step whose "
        "`when:` names an event outside the workflow's own triggers will "
        "simply never fire; check the workflow-level `on:` if a step goes "
        "quiet after migrating."
    ),
    priority=16,
)


def matches(key) -> bool:
    return key == "when"


def apply(key, value, step, ctx, report) -> None:
    condition = when_map.build(value, ctx, report, triggers=False)
    if condition:
        step["if"] = f"{step['if']} && ({condition})" if step.get("if") else condition
        report.mapped(META.id, "when (step)", f"if: {condition}")
