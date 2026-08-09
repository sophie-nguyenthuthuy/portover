"""command / commands — what the step runs."""

from portover.core import MappingMeta

SCOPE = "step"

META = MappingMeta(
    id="command",
    directive="command: / commands:",
    title="Migrate Buildkite command steps to GitHub Actions run steps",
    before="""commands:
  - npm ci
  - npm test""",
    after="""steps:
  - uses: actions/checkout@v4
  - run: npm ci
  - run: npm test""",
    notes=(
        "`command` and `commands` are the same key with two spellings; a "
        "string runs as one command and a list runs one per line. portover "
        "emits one `run:` step each so a failure points at a single command. "
        "Two Buildkite habits need attention afterwards: agents often have "
        "tooling preinstalled that a GitHub-hosted runner does not, so add the "
        "matching setup-* action; and `buildkite-agent` calls inside a command "
        "(artifact upload/download, annotate, meta-data) have no equivalent "
        "binary on a GHA runner — those are flagged separately."
    ),
    priority=10,
)


def matches(key) -> bool:
    return key in ("command", "commands")


def apply(key, value, job, ctx, report) -> None:
    from portover.migrations.buildkite_to_gha import as_list, interpolate, note_vars

    steps = job.setdefault("_script", [])
    count = 0
    for entry in as_list(value):
        command = interpolate(str(entry), ctx)
        note_vars(command, ctx)
        steps.append({"run": command})
        count += 1
    if count:
        report.mapped(META.id, f"{key}: {count} command(s)")
