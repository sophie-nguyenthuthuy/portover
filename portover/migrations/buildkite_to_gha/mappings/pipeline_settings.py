"""env / agents / notify — the pipeline-level keys."""

from portover.core import MappingMeta

SCOPE = "pipeline"

META = MappingMeta(
    id="pipeline-settings",
    directive="env / agents / notify (pipeline level)",
    title="Migrate Buildkite pipeline-level settings to GitHub Actions",
    before="""env:
  BUILD_MODE: release

agents:
  queue: builders

notify:
  - slack: "#builds"
  - github_commit_status:
      context: buildkite""",
    after="""env:
  BUILD_MODE: release        # workflow-level, visible to every job

# agents -> runs-on on each job
# notify -> a final job with if: always(), or GitHub's own
#           commit statuses (which Actions writes for free)""",
    notes=(
        "Pipeline `env:` becomes workflow-level `env:`, the same scope. "
        "`agents:` is a default for every step and is copied onto each job's "
        "`runs-on`. `notify:` mostly disappears in a good way: "
        "`github_commit_status` and `github_check` exist because Buildkite is "
        "external to GitHub, whereas Actions writes commit statuses and checks "
        "natively — there is nothing to port. Slack, email and webhook "
        "notifications do need a step (with `if: failure()` for the common "
        "'tell me when it breaks' case)."
    ),
    priority=12,
)


def matches(key) -> bool:
    return key in ("env", "agents", "notify")


def apply(key, value, ctx, report) -> None:
    from portover.migrations.buildkite_to_gha import as_list, note_vars
    from portover.migrations.buildkite_to_gha.mappings import agents as agents_map

    if key == "env":
        if isinstance(value, dict):
            for name, spec in value.items():
                note_vars(spec, ctx)
                ctx.env[str(name)] = spec
                report.mapped(META.id, f"env.{name}")
        return
    if key == "agents":
        agents_map.apply_pipeline(value, ctx, report)
        return
    for entry in as_list(value):
        name = entry if isinstance(entry, str) else (sorted(entry)[0] if isinstance(entry, dict) else str(entry))
        if str(name) in ("github_commit_status", "github_check"):
            report.mapped(META.id, f"notify: {name}",
                          "dropped — Actions writes commit statuses and checks natively")
            continue
        report.manual(META.id, f"notify: {name}",
                      "add a notifying step (usually `if: failure()`) — e.g. "
                      "slackapi/slack-github-action for Slack, or a curl for a webhook")
