"""version — the config format version."""

from portover.core import MappingMeta

SCOPE = "pipeline"

META = MappingMeta(
    id="version",
    directive="version: 2.1",
    title="Migrate the CircleCI config version key to GitHub Actions",
    before="version: 2.1",
    after="# nothing — GitHub Actions has no config version key",
    notes=(
        "GHA versions the actions you call (actions/checkout@v4), not the "
        "workflow format, so this key simply disappears. It does tell portover "
        "what to expect: 2.1 configs may use orbs, commands, executors and "
        "parameters, while 2.0 configs often have no `workflows:` block at all."
    ),
    priority=5,
)


def matches(key) -> bool:
    return key == "version"


def apply(key, value, ctx, report) -> None:
    report.mapped(META.id, f"version: {value}", "dropped — GHA has no config version key")
