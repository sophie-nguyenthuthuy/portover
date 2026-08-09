"""settings — plugin steps."""

from portover.core import MappingMeta

SCOPE = "step"

META = MappingMeta(
    id="settings",
    directive="settings: (a plugin step)",
    title="Migrate Drone plugins to GitHub Actions",
    before="""- name: publish
  image: plugins/docker
  settings:
    repo: acme/app
    tags: latest
    username: {from_secret: docker_user}
    password: {from_secret: docker_pass}""",
    after="""- uses: docker/login-action@v3
  with:
    username: ${{ secrets.DOCKER_USER }}
    password: ${{ secrets.DOCKER_PASS }}
- uses: docker/build-push-action@v6
  with:
    push: true
    tags: acme/app:latest""",
    notes=(
        "A Drone step with `settings:` and no `commands:` is a plugin — a "
        "container whose behaviour is driven by PLUGIN_* environment "
        "variables. Actions are the direct counterpart and the common plugins "
        "translate: plugins/docker becomes docker/build-push-action (plus "
        "login), plugins/github-release becomes softprops/action-gh-release, "
        "plugins/s3 becomes the AWS CLI after configure-aws-credentials. "
        "Anything unrecognised becomes a visible TODO step carrying its "
        "settings, so nothing is silently dropped — and `from_secret` values "
        "are rewritten to `${{ secrets.* }}` on the way through."
    ),
    priority=18,
)

_HINTS = {
    "plugins/docker": "docker/build-push-action@v6 (with docker/login-action@v3 for the registry)",
    "plugins/ecr": "aws-actions/amazon-ecr-login + docker/build-push-action",
    "plugins/gcr": "google-github-actions/auth + docker/build-push-action",
    "plugins/heroku": "deploy from a run step with a HEROKU_API_KEY secret",
    "plugins/github-release": "softprops/action-gh-release@v2",
    "plugins/gh-pages": "actions/upload-pages-artifact + actions/deploy-pages",
    "plugins/s3": "aws-actions/configure-aws-credentials (OIDC) + `aws s3 sync`",
    "plugins/s3-sync": "aws-actions/configure-aws-credentials (OIDC) + `aws s3 sync`",
    "plugins/slack": "slackapi/slack-github-action@v2 with a webhook secret",
    "plugins/webhook": "a `curl` in a run step",
    "plugins/download": "a `curl` in a run step",
    "plugins/git": "actions/checkout@v4 (already the first step)",
    "plugins/npm": "actions/setup-node with registry-url + `npm publish`",
    "plugins/codecov": "codecov/codecov-action@v4",
    "appleboy/drone-ssh": "appleboy/ssh-action (the key becomes a repository secret)",
    "appleboy/drone-scp": "appleboy/scp-action (the key becomes a repository secret)",
    "plugins/matrix": "no equivalent — use a chat action or a webhook",
    "plugins/telegram": "no official action — use a curl to the Telegram API",
}


def matches(key) -> bool:
    return key == "settings"


def apply(key, value, step, ctx, report) -> None:
    from portover.migrations.drone_to_gha import secret_ref

    image = getattr(ctx, "step_image", "") or "?"
    base = image.split(":")[0]
    settings = {}
    if isinstance(value, dict):
        for name, spec in value.items():
            settings[str(name)] = secret_ref(spec, ctx, report)

    if base == "plugins/git":
        step["_skip"] = True  # checkout is already the job's first step
        report.mapped(META.id, f"plugin: {image}", "dropped — actions/checkout is already the first step")
        return

    if base == "plugins/docker":
        _docker(settings, step, ctx, report, image=image)
        return

    hint = _HINTS.get(base, "no direct equivalent — search the GitHub Marketplace for this plugin")
    report.manual(META.id, f"plugin: {image}",
                  hint + (f"; its settings were {sorted(settings)}" if settings else ""))
    step["run"] = f"echo 'TODO: port Drone plugin {image} — {hint}'\n"
    if settings:
        step["env"] = {f"PLUGIN_{k.upper()}": v for k, v in settings.items()}


def _docker(settings: dict, step, ctx, report, *, image: str) -> None:
    """plugins/docker is common enough to be worth translating properly."""
    repo = settings.get("repo")
    tags = settings.get("tags") or settings.get("tag") or "latest"
    if isinstance(tags, list):
        tag_list = [str(t) for t in tags]
    else:
        tag_list = [t.strip() for t in str(tags).split(",") if t.strip()]
    references = [f"{repo}:{t}" for t in tag_list] if repo else []

    with_: dict = {"push": not settings.get("dry_run", False)}
    if references:
        with_["tags"] = "\n".join(references) if len(references) > 1 else references[0]
    if settings.get("dockerfile"):
        with_["file"] = str(settings["dockerfile"])
    if settings.get("context"):
        with_["context"] = str(settings["context"])
    step["uses"] = "docker/build-push-action@v6"
    step["with"] = with_

    if settings.get("username") or settings.get("password"):
        report.manual(META.id, f"plugin: {image} (registry login)",
                      "add a docker/login-action@v3 step before this one with the same "
                      "username/password secrets")
    report.mapped(META.id, f"plugin: {image}", "docker/build-push-action@v6")
