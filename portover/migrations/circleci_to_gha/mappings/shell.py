"""shell — default shell for job run steps."""

from portover.core import MappingMeta

SCOPE = "job"

META = MappingMeta(
    id="shell", directive="shell: /bin/bash -eo pipefail", title="Migrate the CircleCI job shell",
    before="shell: /bin/bash -eo pipefail", after="""defaults:
  run:
    shell: bash""",
    notes="GHA supplies its own failure flags. Complex CircleCI shell command lines are reduced to the executable and flagged.",
    priority=20,
)


def matches(key) -> bool:
    return key == "shell"


def apply(key, value, job, ctx, report) -> None:
    raw = str(value)
    executable = raw.split()[0].rsplit("/", 1)[-1]
    job.setdefault("defaults", {}).setdefault("run", {})["shell"] = executable
    if len(raw.split()) > 1:
        report.manual(META.id, f"shell: {raw}", f"reduced to `{executable}`; verify its flags")
    else:
        report.mapped(META.id, f"shell: {raw}", executable)
