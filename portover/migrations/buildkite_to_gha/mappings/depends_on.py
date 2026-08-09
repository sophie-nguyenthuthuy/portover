"""depends_on — explicit step dependencies."""

from portover.core import MappingMeta

SCOPE = "step"

META = MappingMeta(
    id="depends-on",
    directive="depends_on: key / [{step, allow_failure}]",
    title="Migrate Buildkite depends_on to GitHub Actions needs",
    before="""- label: Deploy
  depends_on:
    - build
    - step: test
      allow_failure: true""",
    after="""deploy:
  needs: [build, test]
  if: always() && needs.build.result == 'success'""",
    notes=(
        "`depends_on` references step `key:`s and maps onto `needs:` almost "
        "exactly — and in both systems, declaring it opts the step out of the "
        "implicit ordering (Buildkite's wait barriers, which portover would "
        "otherwise apply). The difference is failure handling: "
        "`allow_failure: true` lets the step run even if that dependency "
        "failed, which in GHA needs `if: always()` plus explicit result checks "
        "on the dependencies you still require, because a job with `needs:` is "
        "skipped by default when any dependency fails. Depending on a GROUP "
        "key expands to every job in that group, since GHA cannot depend on a "
        "set."
    ),
    priority=12,
)


def matches(key) -> bool:
    return key in ("depends_on", "allow_dependency_failure")


def apply(key, value, job, ctx, report) -> None:
    if key == "allow_dependency_failure":
        if value:
            job["if"] = f"always() && ({job['if']})" if job.get("if") else "always()"
            report.manual(META.id, "allow_dependency_failure: true",
                          "added `if: always()` — the job now runs even when a dependency fails, "
                          "so check needs.<job>.result for the ones that must have succeeded")
        return
    needs = resolve(value, ctx, report)
    if needs:
        job["needs"] = needs if len(needs) > 1 else needs[0]
        job["_explicit_needs"] = True  # consumed by steps.py: skip barrier ordering
        report.mapped(META.id, f"depends_on: {needs}", "needs:")


def resolve(value, ctx, report) -> list:
    """Turn depends_on entries into GHA job ids."""
    from portover.migrations.buildkite_to_gha import as_list, slug

    out: list = []
    for entry in as_list(value):
        if isinstance(entry, dict):
            name = entry.get("step")
            if entry.get("allow_failure"):
                report.manual(META.id, f"depends_on.{name} allow_failure: true",
                              "add `if: always()` to this job and check "
                              f"needs.{slug(str(name))}.result for the dependencies that must pass")
        else:
            name = entry
        if name is None:
            continue
        target = ctx.keys.get(str(name))
        if target is None:
            target = slug(str(name))
            if target not in ctx.jobs:
                report.manual(META.id, f"depends_on: {name}",
                              "no step with that key was defined before this one — check the job id")
        if isinstance(target, list):  # a group key stands for all its jobs
            out.extend(target)
        else:
            out.append(target)
    return list(dict.fromkeys(out))
