"""script / before_script / after_script — the commands a job runs."""

from portover.core import MappingMeta

SCOPE = "job"

META = MappingMeta(
    id="script",
    directive="script / before_script / after_script",
    title="Migrate GitLab CI script blocks to GitHub Actions run steps",
    before="""before_script:
  - pip install -r requirements.txt
script:
  - pytest -q
  - coverage report
after_script:
  - ./cleanup.sh""",
    after="""steps:
  - uses: actions/checkout@v4
  - run: pip install -r requirements.txt
  - run: pytest -q
  - run: coverage report
  - run: ./cleanup.sh""",
    notes=(
        "Each command becomes its own `run:` step, so the log has the same "
        "shape as GitLab's and a failure points at one command. Two behaviours "
        "do not survive the move and are worth checking: `after_script` in "
        "GitLab runs even when the job fails (add `if: always()` to match), and "
        "it runs in a *fresh shell*, so shell state set earlier is gone — while "
        "in GHA every step shares the runner but not the shell either, so "
        "exported variables need `>> \"$GITHUB_ENV\"`."
    ),
    priority=10,
)


def matches(key) -> bool:
    return key in ("script", "before_script", "after_script")


_BUCKET = {"before_script": "before", "script": "main", "after_script": "after"}


def apply(key, value, job, ctx, report) -> None:
    from portover.migrations.gitlab_ci_to_gha import as_list

    commands = [str(c) for c in as_list(value) if c is not None]
    ctx.scripts[_BUCKET[key]].extend(commands)
    report.mapped(META.id, f"{key}: {len(commands)} command(s)")
    if key == "after_script" and commands:
        report.manual(META.id, "after_script",
                      "GitLab runs after_script even when the job fails — add `if: always()` to those steps to match")
