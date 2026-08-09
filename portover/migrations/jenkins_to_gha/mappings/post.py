"""post — pipeline-level always/success/failure blocks."""

from portover.core import MappingMeta

SCOPE = "pipeline"

META = MappingMeta(
    id="post",
    directive="post { always / success / failure }",
    title="Migrate Jenkins post blocks to GitHub Actions",
    before="""post {
  always  { junit 'reports/**/*.xml' }
  failure { sh './notify.sh' }
}""",
    after="""jobs:
  post:
    needs: [build, test]
    if: always()
    steps:
      - if: ${{ contains(needs.*.result, 'failure') }}
        run: ./notify.sh""",
    notes=(
        "A trailing job with `if: always()` and needs: on every other job. "
        "Inside it, success is `!contains(needs.*.result, 'failure')` and "
        "failure is `contains(needs.*.result, 'failure')` — job-level "
        "success()/failure() would refer to the post job itself."
    ),
    priority=50,  # after stages, so needs: can reference every job
)

_CONDS = {
    "always": None,
    "cleanup": None,
    "success": "${{ !contains(needs.*.result, 'failure') }}",
    "failure": "${{ contains(needs.*.result, 'failure') }}",
    "unstable": "${{ contains(needs.*.result, 'failure') }}",
    "aborted": "${{ contains(needs.*.result, 'cancelled') }}",
}


def matches(node) -> bool:
    return node.keyword() == "post"


def apply(node, ctx, report) -> None:
    from portover.migrations.jenkins_to_gha import convert_steps, new_job

    steps = []
    for cond_block in node.children:
        kw = cond_block.keyword()
        cond = _CONDS.get(kw)
        if kw not in _CONDS:
            report.manual(META.id, cond_block.header, f"post condition '{kw}' not mapped")
            continue
        for s in convert_steps(cond_block, ctx, report):
            steps.append({"if": cond, **s} if cond else s)
        report.mapped(META.id, f"post {{ {kw} }}")
    if not steps:
        return
    job = new_job(ctx, needs=list(ctx.job_order) or None)
    job["if"] = "always()"
    job["steps"] = steps  # no checkout/tools — post steps are usually notify/report
    ctx.workflow["jobs"]["post"] = job
