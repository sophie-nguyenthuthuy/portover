"""jobs / matrix — include, exclude, allow_failures, fast_finish."""

from portover.core import MappingMeta
from portover.migrations.travis_to_gha import parse_env_vars

META = MappingMeta(
    id="matrix-jobs",
    directive="jobs/matrix: include / exclude / allow_failures / fast_finish",
    title="Migrate Travis jobs and matrix customization to GitHub Actions",
    before='jobs:\n  include:\n    - python: "3.13"\n      env: EXPERIMENTAL=1\n  allow_failures:\n    - python: "3.13"\n  fast_finish: true',
    after="""strategy:
  fail-fast: true
  matrix:
    include:
      - python: "3.13"
        env: EXPERIMENTAL=1
# allow_failures: add to the job
#   continue-on-error: ${{ matrix.python == '3.13' }}""",
    notes=(
        "include/exclude rows carry over almost 1:1 (env strings stay strings; "
        "load them like the env matrix rows). allow_failures has no direct key "
        "— it becomes a continue-on-error expression on the job, which portover "
        "writes for single-key rows and flags otherwise. fast_finish is "
        "fail-fast (GHA's default is already true). `stage:` grouping needs "
        "separate jobs with needs: — flagged."
    ),
    priority=45,
)


def matches(key) -> bool:
    return key in ("jobs", "matrix")


def _clean_row(row, ctx, report):
    out = {}
    for k, v in row.items():
        if k == "stage":
            report.manual(META.id, f"stage: {v}", "build stages need separate jobs chained with needs: — split by hand")
        elif k == "env" and isinstance(v, str):
            out["env"] = v
        elif k == "node_js":
            out["node"] = str(v)
        else:
            out[k] = str(v) if not isinstance(v, (bool, int)) else v
    return out


def apply(key, value, ctx, report) -> None:
    if not isinstance(value, dict):
        report.manual(META.id, f"{key}: {value!r}", "unrecognized jobs/matrix shape")
        return
    for row in value.get("include") or []:
        if isinstance(row, dict):
            ctx.matrix_include.append(_clean_row(row, ctx, report))
            report.mapped(META.id, f"include: {row}")
    for row in value.get("exclude") or []:
        if isinstance(row, dict):
            ctx.matrix_exclude.append(_clean_row(row, ctx, report))
            report.mapped(META.id, f"exclude: {row}")
    if "fast_finish" in value:
        report.mapped(META.id, f"fast_finish: {value['fast_finish']}",
                      "fail-fast — GHA already defaults to true")
    for row in value.get("allow_failures") or []:
        if isinstance(row, dict) and len(row) == 1:
            (k, v), = row.items()
            k = {"node_js": "node"}.get(k, k)
            expr = "${{ matrix.%s == '%s' }}" % (k, v)
            job_note = f"add `continue-on-error: {expr}` to the job"
            report.manual(META.id, f"allow_failures: {row}", job_note)
        else:
            report.manual(META.id, f"allow_failures: {row}",
                          "express as a continue-on-error matrix expression by hand")
