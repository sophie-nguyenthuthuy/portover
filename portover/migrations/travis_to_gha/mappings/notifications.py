"""notifications — email/slack/irc."""

from portover.core import MappingMeta

META = MappingMeta(
    id="notifications",
    directive="notifications: email / slack / ...",
    title="Migrate Travis notifications to GitHub Actions",
    before="notifications:\n  email: false\n  slack: myteam:token",
    after="""# GitHub already emails you on failed runs (Settings > Notifications).
# For Slack, add a final step:
- if: failure()
  uses: slackapi/slack-github-action@v2""",
    notes=(
        "email: false is the happy case — GHA only notifies on failure by "
        "default, which is what most people were trying to configure. Slack "
        "tokens embedded in .travis.yml are a secret-hygiene bug anyway: "
        "rotate the token and move it to a repo secret with slackapi's action."
    ),
    priority=55,
)


def matches(key) -> bool:
    return key == "notifications"


def apply(key, value, ctx, report) -> None:
    if not isinstance(value, dict):
        report.mapped(META.id, f"notifications: {value}", "dropped — GHA notifies on failure by default")
        return
    for channel, spec in value.items():
        if channel == "email":
            report.mapped(META.id, f"email: {spec}", "dropped — GHA emails on failure by default; tune in Settings > Notifications")
        elif channel == "slack":
            report.manual(META.id, "notifications.slack",
                          "use slackapi/slack-github-action with a webhook secret — and rotate the token that was sitting in .travis.yml")
        else:
            report.manual(META.id, f"notifications.{channel}", "find the equivalent marketplace action or webhook step")
