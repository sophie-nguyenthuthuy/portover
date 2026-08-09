"""clone — per-step checkout settings."""

from portover.core import MappingMeta

SCOPE = "step"

META = MappingMeta(
    id="clone",
    directive="clone: depth / lfs / enabled",
    title="Migrate Bitbucket Pipelines clone settings to GitHub Actions checkout",
    before="""clone:
  depth: full
  lfs: true""",
    after="""- uses: actions/checkout@v4
  with:
    fetch-depth: 0
    lfs: true""",
    notes=(
        "The defaults differ and it matters: Bitbucket clones 50 commits, GHA "
        "clones 1. Anything reading history — `git describe`, changelog "
        "generation, a diff against the base branch — needs `fetch-depth: 0` "
        "even if the Bitbucket config never mentioned depth. `enabled: false` "
        "means the step gets no source at all, so portover emits no checkout."
    ),
    priority=16,
)


def matches(key) -> bool:
    return key == "clone"


def apply(key, value, job, ctx, report) -> None:
    if not isinstance(value, dict):
        return
    with_: dict = {}
    if value.get("enabled") is False:
        job["_checkout_with"] = None
        job["_no_checkout"] = True
        report.mapped(META.id, "clone.enabled: false", "no checkout step")
        return
    depth = value.get("depth")
    if depth is not None:
        with_["fetch-depth"] = 0 if str(depth) == "full" else int(depth)
        report.mapped(META.id, f"clone.depth: {depth}", f"fetch-depth: {with_['fetch-depth']}")
    if value.get("lfs"):
        with_["lfs"] = True
        report.mapped(META.id, "clone.lfs: true", "lfs: true")
    if with_:
        job["_checkout_with"] = with_
