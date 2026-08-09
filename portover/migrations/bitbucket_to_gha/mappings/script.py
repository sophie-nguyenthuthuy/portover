"""script / after-script — the commands a step runs."""

from portover.core import MappingMeta

SCOPE = "step"

META = MappingMeta(
    id="script",
    directive="script / after-script",
    title="Migrate Bitbucket Pipelines script to GitHub Actions run steps",
    before="""script:
  - npm ci
  - npm test
after-script:
  - ./report.sh""",
    after="""steps:
  - uses: actions/checkout@v4
  - run: npm ci
  - run: npm test
  - if: always()
    run: ./report.sh""",
    notes=(
        "Each command becomes its own `run:` step, so a failure points at one "
        "line the way Bitbucket's log does. `after-script` runs even when the "
        "step failed, which is `if: always()`. One behaviour worth knowing: in "
        "Bitbucket, `after-script` can read $BITBUCKET_EXIT_CODE to tell "
        "success from failure — in GHA you would branch on "
        "`${{ job.status }}` or split into `if: success()` / `if: failure()` "
        "steps instead."
    ),
    priority=10,
)


def matches(key) -> bool:
    return key in ("script", "after-script")


def apply(key, value, job, ctx, report) -> None:
    from portover.migrations.bitbucket_to_gha import as_list, note_vars
    from portover.migrations.bitbucket_to_gha.mappings import pipe as pipe_map

    bucket = "_script" if key == "script" else "_after_script"
    steps = job.setdefault(bucket, [])
    count = 0
    for entry in as_list(value):
        if isinstance(entry, dict):
            if "pipe" in entry:
                pipe_map.convert(entry, steps, ctx, report, always=(key == "after-script"))
                continue
            report.unmapped.append(f"{key} entry: {sorted(entry)}")
            continue
        command = str(entry)
        note_vars(command, ctx)
        step = {"run": command}
        if key == "after-script":
            step = {"if": "always()", "run": command}
        steps.append(step)
        count += 1
    if count:
        report.mapped(META.id, f"{key}: {count} command(s)")
