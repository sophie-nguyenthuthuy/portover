"""extends — template inheritance."""

from portover.core import MappingMeta

SCOPE = "job"

META = MappingMeta(
    id="extends",
    directive="extends: .template",
    title="Migrate GitLab CI extends to GitHub Actions",
    before=""".tests:
  image: python:3.12
  before_script:
    - pip install -r requirements.txt

unit:
  extends: .tests
  script:
    - pytest -q""",
    after="""jobs:
  unit:
    container: python:3.12       # merged in from .tests
    steps:
      - uses: actions/checkout@v4
      - run: pip install -r requirements.txt
      - run: pytest -q""",
    notes=(
        "GHA jobs cannot inherit from each other, so portover merges the "
        "template into the job at conversion time. The merge follows GitLab's "
        "rule: mappings merge key-by-key (so a job can override just `image:` "
        "inside a shared block) while lists and scalars replace outright. "
        "Multiple parents are merged left to right, and a parent may itself "
        "extend another. If you want to keep the reuse rather than the "
        "flattening, the GHA equivalents are a reusable workflow "
        "(`on: workflow_call`) or a composite action."
    ),
    priority=5,  # must resolve before any other job field is read
)

MAX_DEPTH = 10


def matches(key) -> bool:
    return key == "extends"


def apply(key, value, job, ctx, report) -> None:
    """Already resolved by resolve(); nothing left to emit."""


def resolve(definition: dict, ctx, report, *, job: str = "", depth: int = 0) -> dict:
    """Merge every `extends:` parent into a job definition."""
    from portover.migrations.gitlab_ci_to_gha import as_list, merge

    parents = as_list(definition.get("extends"))
    if not parents:
        return definition
    if depth >= MAX_DEPTH:
        report.manual(META.id, f"{job}: extends", f"inheritance deeper than {MAX_DEPTH} — flatten it by hand")
        return definition

    base: dict = {}
    for parent in parents:
        template = ctx.templates.get(str(parent))
        if template is None:
            report.manual(META.id, f"{job}: extends {parent}",
                          "template not found in this file (defined in an `include:`?) — merge it by hand")
            continue
        base = merge(base, resolve(template, ctx, report, job=str(parent), depth=depth + 1))
    resolved = merge(base, definition)
    resolved.pop("extends", None)
    if base:
        report.mapped(META.id, f"{job}: extends {parents}", f"merged {len(parents)} template(s)")
    return resolved
