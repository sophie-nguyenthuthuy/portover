"""pipe — Bitbucket's reusable step units."""

from portover.core import MappingMeta

SCOPE = "structure"  # invoked from script.py for `- pipe:` entries

META = MappingMeta(
    id="pipe",
    directive="- pipe: atlassian/aws-s3-deploy:1.1.0",
    title="Migrate Bitbucket Pipes to GitHub Actions",
    before="""- pipe: atlassian/slack-notify:2.0.0
  variables:
    WEBHOOK_URL: $SLACK_WEBHOOK
    MESSAGE: "Build finished\"""",
    after="""- uses: slackapi/slack-github-action@v2
  with:
    webhook: ${{ secrets.SLACK_WEBHOOK }}
    # MESSAGE -> payload""",
    notes=(
        "A pipe is a Docker image with inputs — the same idea as an action, so "
        "the common Atlassian pipes have direct counterparts and portover "
        "translates those. Two things always need your attention: pipe "
        "`variables:` are passed as environment variables while action inputs "
        "go under `with:`, so names rarely match one-to-one; and any pipe "
        "variable holding a credential was a Bitbucket repository variable, "
        "which must be recreated as a GitHub secret. A `docker://` pipe is just "
        "a container — run it with `docker run` in a `run:` step. Unrecognised "
        "pipes become a visible TODO step rather than disappearing."
    ),
    manual=True,
    priority=48,
)

_PIPES = {
    "atlassian/slack-notify": "slackapi/slack-github-action@v2 (put the webhook in a secret)",
    "atlassian/aws-s3-deploy": "aws-actions/configure-aws-credentials@v4 (prefer OIDC) + `aws s3 sync` in a run step",
    "atlassian/aws-ecs-deploy": "aws-actions/amazon-ecs-deploy-task-definition@v2 after aws-actions/configure-aws-credentials",
    "atlassian/aws-lambda-deploy": "aws-actions/configure-aws-credentials@v4 + `aws lambda update-function-code`",
    "atlassian/aws-cloudfront-invalidate": "aws-actions/configure-aws-credentials@v4 + `aws cloudfront create-invalidation`",
    "atlassian/azure-web-apps-deploy": "azure/webapps-deploy@v3 after azure/login@v2",
    "atlassian/google-app-engine-deploy": "google-github-actions/deploy-appengine@v2 after google-github-actions/auth",
    "atlassian/ssh-run": "appleboy/ssh-action (the SSH key becomes a repository secret)",
    "atlassian/scp-deploy": "appleboy/scp-action (the SSH key becomes a repository secret)",
    "atlassian/rsync-deploy": "burnett01/rsync-deployments, or rsync from a run step",
    "atlassian/git-secrets-scan": "GitHub secret scanning (a repository setting), or trufflehog",
    "atlassian/trigger-pipeline": "call another workflow with `uses:` (workflow_call) or repository_dispatch",
    "atlassian/bitbucket-upload-file": "actions/upload-artifact@v4",
    "atlassian/npm-publish": "actions/setup-node with registry-url + `npm publish` (NODE_AUTH_TOKEN secret)",
    "atlassian/docker-build-push": "docker/build-push-action@v6 with docker/login-action@v3",
    "sonarsource/sonarcloud-scan": "SonarSource/sonarqube-scan-action",
}

_DIRECT = {
    "atlassian/bitbucket-upload-file": ("actions/upload-artifact@v4", {"filename": "path"}),
}


def matches(key) -> bool:
    return key == "pipe"


def convert(entry: dict, steps: list, ctx, report, *, always: bool = False) -> None:
    from portover.migrations.bitbucket_to_gha import note_vars

    raw = str(entry.get("pipe", ""))
    name = raw.split(":")[0] if not raw.startswith("docker://") else raw
    variables = entry.get("variables") if isinstance(entry.get("variables"), dict) else {}
    for value in variables.values():
        note_vars(value, ctx)

    step: dict = {}
    if always:
        step["if"] = "always()"

    if raw.startswith("docker://"):
        image = raw.removeprefix("docker://")
        env = " ".join(f"-e {k}" for k in variables)
        step["run"] = f"docker run --rm {env} {image}".replace("  ", " ")
        if variables:
            step["env"] = {k: _secretish(k, v) for k, v in variables.items()}
        report.manual(META.id, f"pipe: {raw}",
                      "a plain container pipe — converted to `docker run`; check the image's expected inputs")
        steps.append(step)
        return

    direct = _DIRECT.get(name)
    if direct:
        action, input_map = direct
        step["uses"] = action
        with_ = {gha: str(variables[src]) for src, gha in input_map.items() if src in variables}
        if with_:
            step["with"] = with_
        report.mapped(META.id, f"pipe: {raw}", action)
        steps.append(step)
        return

    hint = _PIPES.get(name, "no direct equivalent — search the GitHub Marketplace for this pipe's action")
    report.manual(META.id, f"pipe: {raw}", hint + (f"; its variables were {sorted(variables)}" if variables else ""))
    step["run"] = f"echo 'TODO: port Bitbucket pipe {raw} — {hint}'"
    if variables:
        step["env"] = {k: _secretish(k, v) for k, v in variables.items()}
    steps.append(step)


def _secretish(name: str, value):
    """A pipe variable that forwards $SOMETHING is almost always a repo variable."""
    text = str(value)
    if text.startswith("$") and text[1:].strip("{}").isidentifier():
        return "${{ secrets.%s }}" % text.strip("${}")
    return value
