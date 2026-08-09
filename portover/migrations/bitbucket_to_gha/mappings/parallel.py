"""parallel — concurrent steps."""

from portover.core import MappingMeta

SCOPE = "structure"  # expanded by pipelines.py, not dispatched on a key

META = MappingMeta(
    id="parallel",
    directive="- parallel: [steps] / - parallel: {fail-fast, steps}",
    title="Migrate Bitbucket Pipelines parallel steps to GitHub Actions",
    before="""- parallel:
    fail-fast: true
    steps:
      - step:
          name: Unit
          script: [make unit]
      - step:
          name: Lint
          script: [make lint]""",
    after="""jobs:
  unit:
    needs: build     # both siblings share the previous step's needs
    steps: [...]
  lint:
    needs: build
    steps: [...]""",
    notes=(
        "The direction of the translation is inverted: Bitbucket runs steps "
        "sequentially and `parallel:` is how you opt into concurrency, while "
        "GHA runs jobs concurrently and `needs:` is how you opt into order. So "
        "a parallel block simply becomes sibling jobs that share the same "
        "`needs:`, and the step after the block needs all of them. `fail-fast` "
        "has no per-group equivalent — GHA's `strategy.fail-fast` only applies "
        "to a matrix — so with `fail-fast: false` the siblings keep running "
        "anyway (matching Bitbucket), and with `fail-fast: true` you would need "
        "to cancel the run yourself; portover flags that case."
    ),
    priority=45,
)


def matches(key) -> bool:
    return key == "parallel"


def expand(value, ctx, report, *, index: int, taken: set):
    """Return ([(jid, job)], next_index) for a parallel block."""
    from portover.migrations.bitbucket_to_gha import as_list, build_step

    if isinstance(value, dict):
        steps = as_list(value.get("steps"))
        if value.get("fail-fast"):
            report.manual(META.id, "parallel.fail-fast: true",
                          "GHA cannot cancel sibling jobs on first failure (fail-fast is matrix-only) — "
                          "the other jobs will run to completion")
        else:
            report.mapped(META.id, "parallel block", "sibling jobs sharing one needs:")
    else:
        steps = as_list(value)
        report.mapped(META.id, "parallel block", "sibling jobs sharing one needs:")

    group = []
    for entry in steps:
        if not isinstance(entry, dict) or "step" not in entry:
            continue
        jid, job = build_step(entry["step"] or {}, ctx, report, index=index, taken=taken)
        group.append((jid, job))
        index += 1
    return group, index
