"""matrix — build variants."""

from portover.core import MappingMeta

SCOPE = "pipeline"

META = MappingMeta(
    id="matrix",
    directive="matrix: {VAR: [...], include: [...]}",
    title="Migrate Woodpecker matrix to GitHub Actions",
    before="""matrix:
  GO_VERSION:
    - "1.21"
    - "1.22"
  DATABASE:
    - postgres
    - mysql

steps:
  - name: test
    image: golang:${GO_VERSION}
    commands:
      - go test -tags $DATABASE ./...""",
    after="""strategy:
  matrix:
    GO_VERSION: ["1.21", "1.22"]
    DATABASE: [postgres, mysql]
env:
  GO_VERSION: ${{ matrix.GO_VERSION }}   # so $GO_VERSION still works
  DATABASE: ${{ matrix.DATABASE }}
container: golang:${{ matrix.GO_VERSION }}""",
    notes=(
        "Both build a cartesian product from named variables, so the axes "
        "carry over directly, and `include:` rows map onto matrix `include:`. "
        "The part worth understanding is how the values are read: Woodpecker "
        "exposes each matrix variable as an ENVIRONMENT variable inside the "
        "step, which is why commands say `$GO_VERSION`. portover keeps that "
        "working by defining the job's `env:` from the matrix, so no command "
        "needs editing. The exception is `image:`, which GHA evaluates itself "
        "rather than through a shell — there the `${VAR}` is rewritten to "
        "`${{ matrix.VAR }}`."
    ),
    priority=10,  # before every other field, which interpolates against its keys
)


def matches(key) -> bool:
    return key == "matrix"


def apply(key, value, job, ctx, report) -> None:
    from portover.migrations.woodpecker_to_gha import as_list

    if not isinstance(value, dict):
        report.manual(META.id, f"matrix: {value!r}", "expected named matrix variables")
        return
    matrix: dict = {}
    includes = []
    for name, spec in value.items():
        if name == "include":
            for row in as_list(spec):
                if isinstance(row, dict):
                    includes.append({str(k): v for k, v in row.items()})
                    ctx.matrix_keys.update(str(k) for k in row)
            continue
        values = [v for v in as_list(spec)]
        if not values:
            continue
        matrix[str(name)] = values
        ctx.matrix_keys.add(str(name))
    if includes:
        matrix["include"] = includes
    if not matrix:
        return
    job.setdefault("strategy", {})["matrix"] = matrix
    # Woodpecker exposes matrix values as env vars, so commands read $VAR
    env = job.setdefault("env", {})
    for name in sorted(ctx.matrix_keys):
        env[name] = "${{ matrix.%s }}" % name
    axes = sorted(k for k in matrix if k != "include")
    report.mapped(META.id, f"matrix {axes}", "strategy.matrix + env so $VAR keeps working")
    if includes:
        report.mapped(META.id, f"matrix.include ({len(includes)} row(s))", "matrix.include")
