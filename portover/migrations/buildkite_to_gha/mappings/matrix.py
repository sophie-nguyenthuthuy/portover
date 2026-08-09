"""matrix / parallelism — step fan-out."""

from portover.core import MappingMeta

SCOPE = "step"

META = MappingMeta(
    id="matrix",
    directive="matrix: (list or setup/adjustments) / parallelism: N",
    title="Migrate Buildkite matrix and parallelism to GitHub Actions",
    before="""matrix:
  setup:
    os: [linux, macos]
    version: ["3.11", "3.12"]
command: pytest --os {{matrix.os}} -V {{matrix.version}}

# or a plain count:
parallelism: 4""",
    after="""strategy:
  matrix:
    os: [linux, macos]
    version: ["3.11", "3.12"]
steps:
  - run: pytest --os ${{ matrix.os }} -V ${{ matrix.version }}

# a plain count becomes an index matrix:
strategy:
  matrix:
    BUILDKITE_PARALLEL_JOB: [0, 1, 2, 3]""",
    notes=(
        "Both build a cartesian product, and portover rewrites the "
        "interpolation as it goes: `{{matrix}}` (the single-dimension form) "
        "becomes `${{ matrix.value }}` and `{{matrix.os}}` becomes "
        "`${{ matrix.os }}`. `adjustments:` have no direct equivalent — a "
        "`skip:` adjustment maps onto matrix `exclude:`, while one that only "
        "tweaks a combination's settings maps onto `include:`, so those are "
        "reported rather than guessed. `parallelism: N` splits one step across "
        "N agents and works only because Buildkite sets "
        "BUILDKITE_PARALLEL_JOB/BUILDKITE_PARALLEL_JOB_COUNT for your test "
        "runner to shard on — portover recreates both from the matrix so the "
        "command keeps working (note the index is 0-based, as in Buildkite)."
    ),
    priority=16,
)


def matches(key) -> bool:
    return key in ("matrix", "parallelism")


def apply(key, value, job, ctx, report) -> None:
    from portover.migrations.buildkite_to_gha import as_list

    if key == "parallelism":
        try:
            count = int(value)
        except (TypeError, ValueError):
            report.manual(META.id, f"parallelism: {value!r}", "expected a count")
            return
        job.setdefault("strategy", {})["matrix"] = {"BUILDKITE_PARALLEL_JOB": list(range(count))}
        env = job.setdefault("env", {})
        env["BUILDKITE_PARALLEL_JOB"] = "${{ matrix.BUILDKITE_PARALLEL_JOB }}"
        env["BUILDKITE_PARALLEL_JOB_COUNT"] = count
        ctx.matrix_vars.add("BUILDKITE_PARALLEL_JOB")
        ctx.provided_vars.update({"BUILDKITE_PARALLEL_JOB", "BUILDKITE_PARALLEL_JOB_COUNT"})
        report.mapped(META.id, f"parallelism: {count}",
                      f"{count}-way matrix with BUILDKITE_PARALLEL_JOB/_COUNT")
        return

    if isinstance(value, list):  # single-dimension shorthand
        job.setdefault("strategy", {})["matrix"] = {"value": [str(v) for v in value]}
        ctx.matrix_vars.add("value")
        report.mapped(META.id, f"matrix: {len(value)} value(s)", "strategy.matrix.value")
        return
    if not isinstance(value, dict):
        return
    setup = value.get("setup")
    if isinstance(setup, list):
        job.setdefault("strategy", {})["matrix"] = {"value": [str(v) for v in setup]}
        ctx.matrix_vars.add("value")
        report.mapped(META.id, "matrix.setup (list)", "strategy.matrix.value")
    elif isinstance(setup, dict):
        matrix = {str(k): [str(v) for v in as_list(vals)] for k, vals in setup.items()}
        job.setdefault("strategy", {})["matrix"] = matrix
        ctx.matrix_vars.update(matrix)
        report.mapped(META.id, f"matrix.setup {sorted(matrix)}", "strategy.matrix")
    for adjustment in as_list(value.get("adjustments")):
        if not isinstance(adjustment, dict):
            continue
        combination = adjustment.get("with")
        if adjustment.get("skip"):
            target = job.setdefault("strategy", {}).setdefault("matrix", {}).setdefault("exclude", [])
            if isinstance(combination, dict):
                target.append({str(k): str(v) for k, v in combination.items()})
                report.mapped(META.id, f"matrix adjustment skip: {combination}", "matrix.exclude")
            continue
        report.manual(META.id, f"matrix adjustment: {combination}",
                      "an adjustment that changes a combination's settings — express it as a "
                      "matrix `include:` row, or as an `if:` on the step it affects")
