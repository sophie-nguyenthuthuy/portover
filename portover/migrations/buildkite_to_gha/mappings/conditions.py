"""if / branches / skip — when a step runs."""

from portover.core import MappingMeta
from portover.migrations.buildkite_to_gha.expr import translate

SCOPE = "step"

META = MappingMeta(
    id="conditions",
    directive="if: / branches: / skip:",
    title="Migrate Buildkite if, branches and skip to GitHub Actions",
    before="""if: build.branch == "main" && build.tag == null
branches: "main release/*"
skip: "not ready\"""",
    after="""if: github.ref_name == 'main' && github.ref_type != 'tag'""",
    notes=(
        "Buildkite's `if:` language is already infix, so it reads close to a "
        "GHA expression once the operands are swapped: build.branch -> "
        "github.ref_name, build.commit -> github.sha, "
        "build.pull_request.id != null -> github.event_name == 'pull_request'. "
        "`build.tag == null` is the one that changes shape — in GHA that is a "
        "statement about the ref TYPE (github.ref_type != 'tag'). The older "
        "`branches:` filter is a space-separated glob list where a leading `!` "
        "excludes, which becomes an OR of ref comparisons. `skip:` takes a "
        "string reason in Buildkite and shows it in the UI; GHA has no skipped-"
        "with-reason state, so it becomes `if: false` with the reason kept as a "
        "comment-worthy flag."
    ),
    priority=14,
)


def matches(key) -> bool:
    return key in ("if", "branches", "skip")


def apply(key, value, job, ctx, report) -> None:
    if key == "if":
        condition = translate(value, report, META.id)
        if condition:
            job["if"] = f"{job['if']} && {condition}" if job.get("if") else condition
            report.mapped(META.id, f"if: {value}", condition)
        return
    if key == "skip":
        if value is False:
            return
        job["if"] = "false"
        reason = f" ({value})" if isinstance(value, str) else ""
        report.manual(META.id, f"skip: {value}",
                      f"GHA has no skipped-with-reason state — set `if: false`{reason}, or delete the job")
        return
    _branches(value, job, ctx, report)


def _branches(value, job, ctx, report) -> None:
    from portover.migrations.buildkite_to_gha import as_list

    patterns = []
    for entry in as_list(value):
        patterns.extend(str(entry).split())
    includes, excludes = [], []
    for pattern in patterns:
        negated = pattern.startswith("!")
        text = pattern.lstrip("!")
        rendered = _match(text)
        (excludes if negated else includes).append(rendered)
        report.mapped(META.id, f"branches: {pattern}", rendered)
    conditions = []
    if includes:
        conditions.append(includes[0] if len(includes) == 1 else "(" + " || ".join(includes) + ")")
    conditions.extend(f"!({e})" for e in excludes)
    if conditions:
        joined = " && ".join(conditions)
        job["if"] = f"{job['if']} && {joined}" if job.get("if") else joined


def _match(pattern: str) -> str:
    if pattern.endswith("*"):
        return f"startsWith(github.ref_name, '{pattern.rstrip('*')}')"
    return f"github.ref_name == '{pattern}'"
