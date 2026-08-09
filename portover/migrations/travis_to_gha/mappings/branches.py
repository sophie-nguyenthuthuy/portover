"""branches — only / except."""

from portover.core import MappingMeta

META = MappingMeta(
    id="branches",
    directive="branches: only / except",
    title="Migrate Travis branches to GitHub Actions on.push.branches",
    before="branches:\n  only:\n    - main\n    - /^release-.*$/",
    after='on:\n  push:\n    branches: [main, "release-*"]\n  pull_request:',
    notes=(
        "Travis regexes (/.../) become glob patterns — portover converts the "
        "common ^prefix-.*$ shape and flags anything fancier. `except` maps to "
        "branches-ignore. PRs: Travis built PRs regardless of this setting, so "
        "`pull_request:` is kept unfiltered."
    ),
    priority=16,
)


def matches(key) -> bool:
    return key == "branches"


def _pattern(b, report):
    s = str(b)
    if s.startswith("/") and s.endswith("/"):
        glob = s.strip("/").removeprefix("^").removesuffix("$").replace(".*", "*")
        if any(c in glob for c in "\\()[]+?|"):
            report.manual(META.id, f"branch regex {s}", "regex too rich for glob syntax — translate by hand")
            return None
        report.mapped(META.id, s, f'glob "{glob}"')
        return glob
    report.mapped(META.id, s)
    return s


def apply(key, value, ctx, report) -> None:
    if not isinstance(value, dict):
        return
    on = ctx.workflow["on"]
    push = on.setdefault("push", {})
    for mode, gha_key in (("only", "branches"), ("except", "branches-ignore")):
        entries = value.get(mode) or []
        pats = [p for p in (_pattern(b, report) for b in entries) if p]
        if pats:
            push[gha_key] = pats
    on.setdefault("pull_request", {})
