"""interruptible / resource_group — cancellation and mutual exclusion."""

from portover.core import MappingMeta

SCOPE = "job"

META = MappingMeta(
    id="concurrency",
    directive="interruptible: true / resource_group: production",
    title="Migrate GitLab CI interruptible and resource_group to GitHub Actions",
    before="""interruptible: true
resource_group: production""",
    after="""concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true      # interruptible

# resource_group (never two at once, no cancelling):
concurrency:
  group: production
  cancel-in-progress: false""",
    notes=(
        "Both GitLab directives land on GHA's single `concurrency` key, but "
        "they mean opposite things and portover keeps them apart: "
        "`interruptible` cancels a superseded run (cancel-in-progress: true), "
        "while `resource_group` serialises runs so a deploy is never "
        "concurrent with another (cancel-in-progress: false). Because "
        "portover writes concurrency at the workflow level, a resource_group "
        "on one job serialises the whole workflow — move it to that job's own "
        "`concurrency:` block if that is too broad."
    ),
    priority=46,
)


def matches(key) -> bool:
    return key in ("interruptible", "resource_group")


def apply(key, value, job, ctx, report) -> None:
    if key == "interruptible":
        if not value:
            report.mapped(META.id, "interruptible: false", "the GHA default — runs are not cancelled")
            return
        ctx.concurrency.setdefault("group", "${{ github.workflow }}-${{ github.ref }}")
        ctx.concurrency["cancel-in-progress"] = True
        report.mapped(META.id, "interruptible: true", "concurrency.cancel-in-progress")
        return
    group = str(value)
    job["concurrency"] = {"group": group, "cancel-in-progress": False}
    report.manual(META.id, f"resource_group: {group}",
                  "added a job-level concurrency group so runs serialise — verify the scope is what you want")
