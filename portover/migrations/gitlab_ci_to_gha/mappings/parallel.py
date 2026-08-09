"""parallel — job fan-out, by count or by matrix."""

from portover.core import MappingMeta

SCOPE = "job"

META = MappingMeta(
    id="parallel",
    directive="parallel: N / parallel: matrix:",
    title="Migrate GitLab CI parallel to GitHub Actions matrix",
    before="""parallel:
  matrix:
    - PYTHON: ["3.11", "3.12"]
      OS: [linux]

# or a plain count:
parallel: 4""",
    after="""strategy:
  matrix:
    PYTHON: ["3.11", "3.12"]
    OS: [linux]

# a plain count becomes an index matrix:
strategy:
  matrix:
    CI_NODE_INDEX: [1, 2, 3, 4]
env:
  CI_NODE_TOTAL: 4""",
    notes=(
        "`parallel: matrix:` maps onto `strategy.matrix` almost exactly — the "
        "difference is that GitLab takes a LIST of variable sets (each entry is "
        "its own product) while GHA takes one mapping plus `include:`, so "
        "portover puts the first entry in the matrix and the rest under "
        "`include:`. A plain `parallel: N` splits one job across N runners, and "
        "the split only works because GitLab sets CI_NODE_INDEX/CI_NODE_TOTAL "
        "for your test runner to shard on — portover recreates both from the "
        "matrix so the existing command keeps working."
    ),
    priority=30,
)


def matches(key) -> bool:
    return key == "parallel"


def apply(key, value, job, ctx, report) -> None:
    from portover.migrations.gitlab_ci_to_gha import as_list

    if isinstance(value, dict) and value.get("matrix") is not None:
        entries = [e for e in as_list(value["matrix"]) if isinstance(e, dict)]
        if not entries:
            return
        matrix = {k: as_list(v) for k, v in entries[0].items()}
        if len(entries) > 1:
            matrix["include"] = [{k: (v[0] if isinstance(v, list) and len(v) == 1 else v)
                                  for k, v in e.items()} for e in entries[1:]]
            report.manual(META.id, "parallel.matrix (multiple sets)",
                          "GitLab takes several variable sets; the extra ones became matrix `include:` rows — check the product")
        job.setdefault("strategy", {})["matrix"] = matrix
        report.mapped(META.id, f"parallel.matrix {sorted(k for k in matrix if k != 'include')}", "strategy.matrix")
        return

    try:
        count = int(value)
    except (TypeError, ValueError):
        report.manual(META.id, f"parallel: {value!r}", "expected a count or a matrix")
        return
    job.setdefault("strategy", {})["matrix"] = {"CI_NODE_INDEX": list(range(1, count + 1))}
    job.setdefault("env", {})["CI_NODE_INDEX"] = "${{ matrix.CI_NODE_INDEX }}"
    job.setdefault("env", {})["CI_NODE_TOTAL"] = count
    report.mapped(META.id, f"parallel: {count}", f"{count}-way matrix with CI_NODE_INDEX/CI_NODE_TOTAL")
