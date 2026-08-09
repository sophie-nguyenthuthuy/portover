"""wait — the pipeline barrier."""

from portover.core import MappingMeta

SCOPE = "structure"  # consumed by steps.py, not dispatched on a key

META = MappingMeta(
    id="wait",
    directive="- wait / - wait: {continue_on_failure: true}",
    title="Migrate Buildkite wait steps to GitHub Actions needs",
    before="""steps:
  - label: Unit
    command: make unit
  - label: Lint
    command: make lint
  - wait
  - label: Deploy
    command: ./deploy.sh""",
    after="""jobs:
  unit:   { steps: [...] }     # no needs — parallel by default
  lint:   { steps: [...] }
  deploy:
    needs: [unit, lint]        # the wait barrier, expressed per job
    steps: [...]""",
    notes=(
        "`wait` is the one construct with no GHA counterpart: GHA has no "
        "barrier, only per-job dependencies. portover therefore expands it — "
        "every step after the wait gains a `needs:` listing every step before "
        "it. That reproduces the ordering exactly, at the cost of a longer "
        "`needs:` list than a barrier would need. `continue_on_failure: true` "
        "(run the following steps even if earlier ones failed) becomes "
        "`if: always()` on those jobs, because a GHA job with `needs:` "
        "otherwise skips when a dependency fails."
    ),
    priority=42,
)


def matches(key) -> bool:
    return key == "wait"


def barrier(spec, ctx, report) -> None:
    """Everything after this point waits for everything before it."""
    if not ctx.barrier:
        report.mapped(META.id, "wait", "no preceding steps — nothing to wait for")
        return
    ctx.pending_needs = list(ctx.barrier)
    ctx.barrier = []
    detail = f"following steps need {ctx.pending_needs}"
    if isinstance(spec, dict) and spec.get("continue_on_failure"):
        ctx.continue_on_failure = True
        report.manual(META.id, "wait.continue_on_failure: true",
                      "add `if: always()` to the jobs after this barrier — a GHA job with needs: "
                      "is skipped when a dependency fails")
    else:
        report.mapped(META.id, "wait", detail)
