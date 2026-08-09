"""strategy — matrix and parallel fan-out."""

from portover.core import MappingMeta

SCOPE = "job"

META = MappingMeta(
    id="strategy",
    directive="strategy: matrix / parallel / maxParallel",
    title="Migrate Azure Pipelines strategy matrix to GitHub Actions",
    before="""strategy:
  matrix:
    Python311:
      python.version: "3.11"
    Python312:
      python.version: "3.12"
  maxParallel: 2""",
    after="""strategy:
  max-parallel: 2
  matrix:
    include:
      - python_version: "3.11"
      - python_version: "3.12\"""",
    notes=(
        "The shapes differ: Azure names each combination explicitly (a mapping "
        "of legName -> variables) while GHA takes axes and multiplies them. "
        "Named legs are therefore emitted as matrix `include:` rows, which "
        "reproduces exactly the combinations listed rather than a cartesian "
        "product. Dots in Azure variable names (`python.version`) are not valid "
        "in GHA matrix keys, so they become underscores — update the references "
        "in your scripts to match. `maxParallel` is `max-parallel`; a plain "
        "`parallel: N` (slicing one job across agents) has no equivalent and is "
        "flagged."
    ),
    priority=20,
)


def matches(key) -> bool:
    return key == "strategy"


def apply(key, value, job, ctx, report) -> None:
    if not isinstance(value, dict):
        return
    strategy: dict = {}
    matrix = value.get("matrix")
    if isinstance(matrix, dict):
        rows = []
        for leg, variables in matrix.items():
            if not isinstance(variables, dict):
                continue
            row = {str(k).replace(".", "_"): v for k, v in variables.items()}
            row.setdefault("leg", str(leg))
            ctx.matrix_vars.update(row)  # so $(python.version) resolves to matrix, not env
            rows.append(row)
        if rows:
            renamed = [k for row in rows for k in row if "_" in k]
            strategy["matrix"] = {"include": rows}
            report.mapped(META.id, f"strategy.matrix ({len(rows)} legs)", "matrix.include rows")
            if renamed:
                report.manual(META.id, "matrix variable names",
                              "dots are not allowed in GHA matrix keys — they became underscores "
                              "(reference them as ${{ matrix.python_version }})")
    elif matrix is not None:
        report.manual(META.id, f"strategy.matrix: {matrix!r}", "expected named matrix legs")

    if value.get("maxParallel") is not None:
        strategy["max-parallel"] = int(value["maxParallel"])
        report.mapped(META.id, f"maxParallel: {value['maxParallel']}", "max-parallel")
    if value.get("parallel") is not None:
        report.manual(META.id, f"strategy.parallel: {value['parallel']}",
                      "slicing one job across agents has no GHA equivalent — shard with a matrix "
                      "and your test runner's own sharding flag")
    if strategy:
        job.setdefault("strategy", {}).update(strategy)
