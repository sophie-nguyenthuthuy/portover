"""orbs — the orbs declaration block."""

from portover.core import MappingMeta

SCOPE = "pipeline"

META = MappingMeta(
    id="orbs",
    directive="orbs: name: namespace/orb@x.y",
    title="Migrate CircleCI orbs to GitHub Actions",
    before="""orbs:
  node: circleci/node@5.2.0
  aws-cli: circleci/aws-cli@4.1.3""",
    after="""# orbs have no declaration block — each orb command becomes an action
# at the step that used it:
steps:
  - uses: actions/setup-node@v4      # was: node/install-packages
  - uses: aws-actions/configure-aws-credentials@v4   # was: aws-cli/setup""",
    notes=(
        "Orbs are packaged step bundles; GHA's equivalent unit is the action, "
        "declared inline at the step. portover records the orb aliases here so "
        "each `orb/command` step can be flagged with its orb name — see the "
        "orb-steps page. Common swaps: circleci/node -> actions/setup-node, "
        "circleci/python -> actions/setup-python, circleci/aws-cli -> "
        "aws-actions/configure-aws-credentials (prefer OIDC over stored keys), "
        "circleci/slack -> slackapi/slack-github-action, circleci/docker -> "
        "docker/build-push-action."
    ),
    manual=True,
    priority=12,
)


def matches(key) -> bool:
    return key == "orbs"


def apply(key, value, ctx, report) -> None:
    if not isinstance(value, dict):
        return
    for alias, ref in value.items():
        ctx.orbs[alias] = str(ref)
        report.manual(META.id, f"orbs.{alias}: {ref}",
                      f"no declaration needed — replace each `{alias}/...` step with the equivalent action")
