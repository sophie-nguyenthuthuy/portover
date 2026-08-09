"""Build phases: before_install/install/before_script/script/after_*."""

from portover.core import MappingMeta
from portover.migrations.travis_to_gha import PHASES

META = MappingMeta(
    id="scripts",
    directive="before_install / install / script / after_success / after_failure ...",
    title="Migrate Travis build phases to GitHub Actions steps",
    before="install:\n  - pip install -r requirements.txt\nscript:\n  - pytest -q\nafter_failure:\n  - cat logs/test.log",
    after="""steps:
  - run: pip install -r requirements.txt
  - run: pytest -q
  - if: failure()
    run: cat logs/test.log""",
    notes=(
        "Phases flatten into ordered steps of one job. after_success -> "
        "`if: success()`, after_failure -> `if: failure()`, after_script -> "
        "`if: always()`. One Travis semantic does not carry: after_* results "
        "never affected the Travis build status, but a failing `if:` step DOES "
        "fail the GHA job — append `|| true` if you relied on that."
    ),
    priority=40,
)

_PHASE_NAMES = {name for name, _ in PHASES}


def matches(key) -> bool:
    return key in _PHASE_NAMES


def apply(key, value, ctx, report) -> None:
    cmds = [str(c) for c in (value if isinstance(value, list) else [value]) if c is not None]
    ctx.phases.setdefault(key, []).extend(cmds)
    report.mapped(META.id, f"{key}: {len(cmds)} command(s)")
