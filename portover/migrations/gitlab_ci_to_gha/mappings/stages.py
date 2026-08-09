"""stages — the global stage order."""

from portover.core import MappingMeta

SCOPE = "pipeline"

META = MappingMeta(
    id="stages",
    directive="stages: [build, test, deploy]",
    title="Migrate GitLab CI stages to GitHub Actions needs",
    before="""stages:
  - build
  - test
  - deploy

unit:
  stage: test
lint:
  stage: test
ship:
  stage: deploy""",
    after="""jobs:
  unit:
    needs: build-job     # every job in the previous stage
  lint:
    needs: build-job
  ship:
    needs: [unit, lint]  # waits for the whole test stage""",
    notes=(
        "GHA has no stages — only per-job `needs:`. The translation is "
        "mechanical but inverted: GitLab declares the *sequence* globally and "
        "gets parallelism for free within a stage, while GHA gets parallelism "
        "for free and you declare the sequence per job. portover wires each job "
        "to every job of the previous non-empty stage, which preserves the "
        "ordering exactly. A job with its own `needs:` keeps it — that's already "
        "a DAG. GitLab's implicit `.pre`/`.post` stages are not in the default "
        "list; declare them if you use them."
    ),
    priority=10,
)


def matches(key) -> bool:
    return key in ("stages", "types")


def apply(key, value, ctx, report) -> None:
    from portover.migrations.gitlab_ci_to_gha import as_list

    stages = [str(s) for s in as_list(value)]
    if stages:
        ctx.stages = stages
        report.mapped(META.id, f"{key}: {stages}", "wired as needs: between stages")
    if key == "types":
        report.manual(META.id, "types:", "`types` is the removed alias for `stages` — rename it in the source config")
