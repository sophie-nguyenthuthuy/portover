"""workflows — job ordering, filters, schedules, approval gates."""

import copy

from portover.core import MappingMeta
from portover.emit import yaml_dump

SCOPE = "pipeline"

META = MappingMeta(
    id="workflows",
    directive="workflows: <name>: jobs: [{job: {requires, filters, context}}]",
    title="Migrate CircleCI workflows to GitHub Actions",
    before="""workflows:
  build_test_deploy:
    jobs:
      - build
      - test:
          requires: [build]
      - deploy:
          requires: [test]
          filters:
            branches:
              only: main""",
    after="""# .github/workflows/build_test_deploy.yml
jobs:
  build: { ... }
  test:
    needs: build
    ...
  deploy:
    needs: test
    if: github.ref == 'refs/heads/main'
    ...""",
    notes=(
        "One CircleCI workflow becomes one workflow FILE, because GHA scopes "
        "triggers per file rather than per job. `requires` maps to `needs`. "
        "Filters are the sharp edge: they are per-job in CircleCI but per-file "
        "in GHA, so portover keeps them as job-level `if:` conditions — and "
        "when any job filters on tags it also adds `on: push: tags:`, because "
        "an `if:` alone can never fire on a tag the workflow was not triggered "
        "for. `type: approval` jobs become a GHA environment with required "
        "reviewers (configured in repo settings, not YAML)."
    ),
    priority=50,  # last: needs every job definition to exist first
)


def matches(key) -> bool:
    return key == "workflows"


def _ref_cond(kind: str, spec, report) -> list:
    """branches/tags filter -> one grouped GHA expression."""
    prefix = "refs/heads/" if kind == "branches" else "refs/tags/"
    by_mode = {"only": [], "ignore": []}
    if not isinstance(spec, dict):
        spec = {"only": spec}
    for mode in ("only", "ignore"):
        entries = spec.get(mode)
        if entries is None:
            continue
        for entry in (entries if isinstance(entries, list) else [entries]):
            s = str(entry)
            neg = mode == "ignore"
            if s.startswith("/") and s.endswith("/"):
                body = s.strip("/").removeprefix("^")
                if body.endswith("$"):
                    body = body[:-1]
                    exact = "*" not in body and "." not in body
                else:
                    exact = False
                literal = body.split(".*")[0].split("[")[0].split("(")[0]
                if not literal:
                    report.manual(META.id, f"filter {kind}: {s}",
                                  "regex has no literal prefix — write the `if:` condition by hand")
                    continue
                cond = (f"github.ref == '{prefix}{literal}'" if exact
                        else f"startsWith(github.ref, '{prefix}{literal}')")
                report.mapped(META.id, f"filter {kind}: {s}", f"{'!' if neg else ''}{cond}")
            else:
                cond = f"github.ref == '{prefix}{s}'"
                report.mapped(META.id, f"filter {kind}: {s}")
            by_mode[mode].append(f"!({cond})" if neg else cond)
    groups = []
    if by_mode["only"]:
        groups.append("(" + " || ".join(by_mode["only"]) + ")")
    if by_mode["ignore"]:
        groups.append("(" + " && ".join(by_mode["ignore"]) + ")")
    return [" && ".join(groups)] if groups else []


def _job_entry(entry, ctx, report):
    """Normalize a workflow job entry to (name, options dict)."""
    if isinstance(entry, str):
        return entry, {}
    if isinstance(entry, dict) and len(entry) == 1:
        (name, opts), = entry.items()
        return name, opts if isinstance(opts, dict) else {}
    report.unmapped.append(f"workflows job entry: {entry!r}")
    return None, {}


def apply(key, value, ctx, report) -> None:
    from portover.migrations.circleci_to_gha import CircleCiToGha, slug

    if not isinstance(value, dict):
        return
    for wf_name, wf in value.items():
        if wf_name == "version" or not isinstance(wf, dict):
            continue
        jobs: dict = {}
        on: dict = {}
        tag_filtered = False

        for entry in wf.get("jobs") or []:
            name, opts = _job_entry(entry, ctx, report)
            if name is None:
                continue
            jid = ctx.job_names.get(str(name), slug(name))
            approval = opts.get("type") == "approval"
            if jid not in ctx.job_defs and not approval:
                report.manual(META.id, f"workflows.{wf_name}: {name}",
                              "no matching job definition (an orb-provided job?) — add its steps by hand")
                continue
            job = copy.deepcopy(ctx.job_defs[jid]) if not approval else {}
            conds: list = []

            if approval:
                job = {"runs-on": "ubuntu-latest", "environment": "approval",
                       "steps": [{"run": 'echo "approval gate"'}]}
                report.manual(META.id, f"workflows.{wf_name}: {name} (type: approval)",
                              "create a repo Environment named 'approval' with required reviewers — the gate lives in settings, not YAML")
            requires = opts.get("requires")
            if requires:
                needs = [ctx.job_names.get(str(r), slug(r)) for r in
                         (requires if isinstance(requires, list) else [requires])]
                job["needs"] = needs if len(needs) > 1 else needs[0]
                report.mapped(META.id, f"{name} requires {requires}", f"needs: {needs}")
            if opts.get("context"):
                report.manual(META.id, f"workflows.{wf_name}: {name} context: {opts['context']}",
                              "CircleCI contexts map to repo/org secrets (optionally scoped by a GHA Environment)")
            if opts.get("name"):
                job["name"] = str(opts["name"])
                report.mapped(META.id, f"{name} display name", str(opts["name"]))
            filters = opts.get("filters") or {}
            if isinstance(filters, dict):
                filter_groups = []
                for kind in ("branches", "tags"):
                    if kind in filters:
                        filter_groups.extend(_ref_cond(kind, filters[kind], report))
                        tag_filtered = tag_filtered or kind == "tags"
                if filter_groups:
                    conds.append("(" + " || ".join(filter_groups) + ")")
            matrix = (opts.get("matrix") or {}).get("parameters") if isinstance(opts.get("matrix"), dict) else None
            if isinstance(matrix, dict) and matrix:
                target = job.setdefault("strategy", {}).setdefault("matrix", {})
                target.update({k: list(v) if isinstance(v, list) else [v]
                               for k, v in matrix.items()})
                report.mapped(META.id, f"{name} matrix", f"strategy.matrix {sorted(matrix)}")
            if conds:
                job["if"] = " && ".join(conds)
            for option in set(opts) - {"type", "requires", "context", "filters", "matrix", "name"}:
                report.unmapped.append(f"workflows.{wf_name}.{name}: {option}")
            jobs[jid] = job

        for trigger in wf.get("triggers") or []:
            sched = trigger.get("schedule") if isinstance(trigger, dict) else None
            if isinstance(sched, dict) and sched.get("cron"):
                on.setdefault("schedule", []).append({"cron": str(sched["cron"]).strip()})
                report.mapped(META.id, f"workflows.{wf_name} schedule", f"on.schedule: {sched['cron']}")
        if isinstance(wf.get("when"), (str, dict)):
            report.manual(META.id, f"workflows.{wf_name}: when",
                          "conditional workflow — express it as an `if:` on each job or a separate trigger")
        for option in set(wf) - {"jobs", "triggers", "when"}:
            report.unmapped.append(f"workflows.{wf_name}: {option}")

        if not on:
            on = CircleCiToGha.default_on()
        if tag_filtered:
            on.setdefault("push", {})["tags"] = ["*"]
            report.manual(META.id, f"workflows.{wf_name}: tag filters",
                          "added `on: push: tags: ['*']` — without a tag trigger the job's `if:` could never fire")
        if ctx.inputs:
            on["workflow_dispatch"] = {"inputs": ctx.inputs}
        if not jobs:
            continue
        doc = {"name": str(wf_name), "on": on, "jobs": jobs}
        report.outputs[f".github/workflows/{slug(wf_name)}.yml"] = yaml_dump(doc) + "\n"
        report.mapped(META.id, f"workflows.{wf_name}", f"{len(jobs)} job(s) -> {slug(wf_name)}.yml")
