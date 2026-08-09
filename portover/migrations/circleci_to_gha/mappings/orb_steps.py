"""orb command calls — flag for replacement with a GitHub Action."""

from portover.core import MappingMeta

SCOPE = "step"

META = MappingMeta(
    id="orb-steps", directive="- <orb-alias>/<command>", title="Migrate CircleCI orb command steps",
    before="- node/install-packages", after="""- uses: actions/setup-node@v4
- run: npm ci""",
    notes="Orb commands are arbitrary packaged logic. Portover identifies the source orb but leaves the exact action and inputs for review.",
    manual=True, priority=100,
)


def matches(name) -> bool:
    return isinstance(name, str) and "/" in name


def apply(name, value, out, ctx, report) -> None:
    alias = name.split("/", 1)[0]
    ref = ctx.orbs.get(alias, alias)
    report.manual(META.id, f"step: {name} ({ref})", "replace this orb command with the equivalent action/run steps")
