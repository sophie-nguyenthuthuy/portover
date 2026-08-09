"""rules — the modern per-job conditions."""

from portover.core import MappingMeta
from portover.migrations.gitlab_ci_to_gha.expr import translate

SCOPE = "job"

META = MappingMeta(
    id="rules",
    directive="rules: [{if, changes, exists, when, allow_failure}]",
    title="Migrate GitLab CI rules to GitHub Actions if conditions",
    before="""rules:
  - if: $CI_COMMIT_BRANCH == "main"
  - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    when: manual
  - when: never""",
    after="""if: >-
  github.ref_name == 'main' ||
  github.event_name == 'pull_request'""",
    notes=(
        "The semantics differ in a way that matters: GitLab evaluates rules "
        "top-down and stops at the FIRST match, so a later rule never overrides "
        "an earlier one. GHA has a single `if:` per job. portover ORs together "
        "the conditions that include the job and negates any `when: never` rule "
        "that precedes them, which reproduces first-match for the shapes people "
        "actually write. A trailing bare `when: never` is just 'nothing else "
        "runs' and needs no output. Per-rule `when: manual` cannot be folded "
        "into a boolean at all — that job wants a workflow_dispatch trigger or "
        "an environment with required reviewers, so it is flagged. Variables "
        "are translated to github contexts: $CI_COMMIT_BRANCH -> "
        "github.ref_name, $CI_PIPELINE_SOURCE == \"merge_request_event\" -> "
        "github.event_name == 'pull_request'."
    ),
    priority=20,
)


def matches(key) -> bool:
    return key == "rules"


def apply(key, value, job, ctx, report) -> None:
    from portover.migrations.gitlab_ci_to_gha import as_list

    includes: list = []
    excludes: list = []
    for rule in as_list(value):
        if not isinstance(rule, dict):
            if isinstance(rule, str):
                report.manual(META.id, f"rules: {rule}", "expected a mapping with if/changes/when")
            continue
        when = str(rule.get("when", "on_success"))
        condition = rule.get("if")

        if "changes" in rule:
            _changes(rule["changes"], report)
        if "exists" in rule:
            report.manual(META.id, f"rules exists: {rule['exists']}",
                          "no file-existence condition — test it in a step and gate later steps on its output")
        if rule.get("allow_failure") is not None:
            job["continue-on-error"] = bool(rule["allow_failure"])
            report.mapped(META.id, f"rules allow_failure: {rule['allow_failure']}", "continue-on-error")

        if condition is None:
            if when == "never" and not includes:
                continue  # trailing "nothing else runs"
            if when == "manual":
                _manual(job, report, "rules: when: manual")
            continue

        translated = translate(str(condition), report, META.id)
        if translated is None:
            continue
        if when == "never":
            excludes.append(translated)
        else:
            includes.append(translated)
            report.mapped(META.id, f"rules if: {condition}", translated)
            if when == "manual":
                _manual(job, report, f"rules: when: manual ({condition})")
            elif when == "always":
                includes[-1] = f"({translated}) || always()"

    conditions = []
    if excludes:
        conditions.extend(f"!({e})" for e in excludes)
    if includes:
        conditions.append(includes[0] if len(includes) == 1 else "(" + " || ".join(includes) + ")")
    if conditions:
        job["if"] = " && ".join(conditions)


def _changes(changes, report) -> None:
    from portover.migrations.gitlab_ci_to_gha import as_list

    paths = as_list(changes if not isinstance(changes, dict) else changes.get("paths"))
    report.manual(META.id, f"rules changes: {[str(p) for p in paths]}",
                  "GHA path filters are per-workflow (`on: push: paths:`) — for a per-job filter "
                  "use dorny/paths-filter and gate the job on its output")


def _manual(job, report, source: str) -> None:
    report.manual(META.id, source,
                  "a manual job — add `workflow_dispatch` to on:, or put the job behind an "
                  "environment with required reviewers")
