"""workflow — pipeline-level rules that decide whether the pipeline runs at all."""

from portover.core import MappingMeta
from portover.migrations.gitlab_ci_to_gha.expr import PIPELINE_SOURCE, translate

SCOPE = "pipeline"

META = MappingMeta(
    id="workflow-rules",
    directive="workflow: rules / name",
    title="Migrate GitLab CI workflow rules to GitHub Actions triggers",
    before="""workflow:
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == "main"
    - if: $CI_COMMIT_TAG
    - when: never""",
    after="""on:
  pull_request:
  push:
    branches: [main]
    tags: ["*"]""",
    notes=(
        "This is the one place where GitLab rules become GHA *triggers* rather "
        "than `if:` conditions, because they decide whether the run happens at "
        "all. portover reads the rule list for the pipeline sources and branch/"
        "tag conditions it can recognise and builds `on:` from them; a trailing "
        "`when: never` is the GitLab idiom for 'nothing else runs' and needs no "
        "translation, since GHA only triggers on what you list. Anything more "
        "involved is flagged — an over-broad trigger is a wasted run, but a "
        "wrong one silently stops building."
    ),
    priority=18,
)


def matches(key) -> bool:
    return key == "workflow"


def apply(key, value, ctx, report) -> None:
    from portover.migrations.gitlab_ci_to_gha import as_list

    if not isinstance(value, dict):
        return
    if value.get("name"):
        report.mapped(META.id, "workflow.name", "run names come from `run-name:` in GHA")
    on: dict = {}
    for rule in as_list(value.get("rules")):
        if not isinstance(rule, dict):
            continue
        if rule.get("when") == "never" and "if" not in rule:
            continue
        condition = rule.get("if")
        if condition is None:
            if "changes" in rule:
                _paths(rule["changes"], on, report)
            continue
        _from_condition(str(condition), rule, on, report)
    if on:
        ctx.on.update(on)
        report.mapped(META.id, "workflow.rules", f"on: {sorted(on)}")


def _paths(changes, on: dict, report) -> None:
    from portover.migrations.gitlab_ci_to_gha import as_list

    paths = [str(p) for p in as_list(changes if not isinstance(changes, dict) else changes.get("paths"))]
    if paths:
        on.setdefault("push", {})["paths"] = paths
        report.mapped(META.id, f"workflow changes: {paths}", "on.push.paths")


def _from_condition(condition: str, rule: dict, on: dict, report) -> None:
    if rule.get("when") == "never":
        report.manual(META.id, f"workflow rule never: {condition}",
                      "an exclusion rule — GHA has no negative trigger; use paths-ignore/branches-ignore or an `if:` on each job")
        return
    for source, event in PIPELINE_SOURCE.items():
        if f'"{source}"' in condition or f"'{source}'" in condition:
            on.setdefault(event, {})
            report.mapped(META.id, f"workflow rule: {condition}", f"on.{event}")
            return
    if "CI_COMMIT_TAG" in condition:
        on.setdefault("push", {}).setdefault("tags", ["*"])
        report.mapped(META.id, f"workflow rule: {condition}", "on.push.tags")
        return
    if "CI_COMMIT_BRANCH" in condition or "CI_COMMIT_REF_NAME" in condition:
        branch = _branch_literal(condition)
        if branch:
            on.setdefault("push", {}).setdefault("branches", []).append(branch)
            report.mapped(META.id, f"workflow rule: {condition}", f"on.push.branches += {branch}")
            return
        on.setdefault("push", {})
        report.manual(META.id, f"workflow rule: {condition}",
                      "branch condition kept as a broad `on: push` — narrow it with branches: if that matters")
        return
    translated = translate(condition, report, META.id)
    if translated:
        on.setdefault("push", {})
        report.manual(META.id, f"workflow rule: {condition}",
                      f"no trigger equivalent — as a job condition this would be `if: {translated}`")


def _branch_literal(condition: str) -> str | None:
    for quote in ('"', "'"):
        if quote in condition:
            parts = condition.split(quote)
            if len(parts) >= 2 and parts[1]:
                return parts[1]
    if "CI_DEFAULT_BRANCH" in condition:
        return "main"
    return None
