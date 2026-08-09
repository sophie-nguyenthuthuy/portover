"""env — global vars, secure values, and env matrix rows."""

from portover.core import MappingMeta
from portover.migrations.travis_to_gha import parse_env_vars

META = MappingMeta(
    id="env",
    directive="env / env.global / env.jobs (secure: ...)",
    title="Migrate Travis env to GitHub Actions",
    before='env:\n  global:\n    - REGISTRY=ghcr.io/acme\n    - secure: "encrypted..."\n  jobs:\n    - DB=postgres\n    - DB=sqlite',
    after="""env:
  REGISTRY: ghcr.io/acme
  API_KEY: ${{ secrets.API_KEY }}
strategy:
  matrix:
    env: ["DB=postgres", "DB=sqlite"]
steps:
  - run: tr " " "\\n" <<< "${{ matrix.env }}" >> "$GITHUB_ENV\"""",
    notes=(
        "`secure:` values are Travis-encrypted and CANNOT be decrypted by "
        "anyone but Travis — re-create each one as a repository secret. A "
        "multi-row env list is a build matrix in Travis; portover reproduces it "
        "as a matrix dimension plus one step that loads the row into "
        "$GITHUB_ENV."
    ),
    priority=12,
)


def matches(key) -> bool:
    return key == "env"


def _rows(value):
    return value if isinstance(value, list) else [value]


def apply(key, value, ctx, report) -> None:
    if isinstance(value, dict):
        for row in _rows(value.get("global") or []):
            _one(row, ctx, report, matrix=False)
        for row in _rows(value.get("jobs") or value.get("matrix") or []):
            _one(row, ctx, report, matrix=True)
    else:
        for row in _rows(value):
            _one(row, ctx, report, matrix=True)


def _one(row, ctx, report, *, matrix: bool) -> None:
    if isinstance(row, dict) and "secure" in row:
        report.manual(META.id, "secure: <encrypted>",
                      "cannot be decrypted outside Travis — re-create it as a repo secret and reference ${{ secrets.NAME }}")
        return
    if not isinstance(row, str):
        report.manual(META.id, str(row), "unrecognized env entry")
        return
    if matrix:
        ctx.env_rows.append(row)
        report.mapped(META.id, row, "env matrix row")
    else:
        ctx.env.update(parse_env_vars(row))
        report.mapped(META.id, row)
