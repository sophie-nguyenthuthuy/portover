"""settings — plugin steps."""

from portover.core import MappingMeta

SCOPE = "step"

META = MappingMeta(
    id="settings",
    directive="settings: (a plugin step)",
    title="Migrate Woodpecker plugins to GitHub Actions",
    before="""- name: publish
  image: woodpeckerci/plugin-docker-buildx
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
        "A step with `settings:` and no `commands:` is a plugin — a container "
        "configured through PLUGIN_* environment variables, which is what an "
        "action does with `with:`. Woodpecker's own plugins live under the "
        "woodpeckerci/ namespace but many configs still use Drone's "
        "plugins/ images, so both are recognised. Unrecognised plugins become "
        "a visible TODO step that keeps their settings as PLUGIN_* env, so "
        "nothing is lost silently, and `from_secret` values are rewritten to "
        "`${{ secrets.* }}` on the way through."
    ),
    priority=18,
)

_HINTS = {
    "plugin-docker-buildx": "docker/build-push-action@v6 (with docker/login-action@v3)",
    "plugin-git": "actions/checkout@v4 (already the first step)",
    "plugin-s3": "aws-actions/configure-aws-credentials (OIDC) + `aws s3 sync`",
    "plugin-github-release": "softprops/action-gh-release@v2",
    "plugin-gitea-release": "no official action — use the Gitea API from a run step",
    "plugin-matrix": "no equivalent — use a chat action or a webhook",
    "plugin-slack": "slackapi/slack-github-action@v2 with a webhook secret",
    "plugin-webhook": "a `curl` in a run step",
    "plugin-codecov": "codecov/codecov-action@v4",
    "plugin-npm": "actions/setup-node with registry-url + `npm publish`",
    "plugin-ssh": "appleboy/ssh-action (the key becomes a repository secret)",
    "plugin-scp": "appleboy/scp-action (the key becomes a repository secret)",
    "plugin-surge-preview": "no equivalent — deploy from a run step",
    "plugin-ready-release-go": "release-please or semantic-release via their actions",
    # Drone-era images still common in Woodpecker configs
    "docker": "docker/build-push-action@v6 (with docker/login-action@v3)",
    "s3": "aws-actions/configure-aws-credentials (OIDC) + `aws s3 sync`",
    "git": "actions/checkout@v4 (already the first step)",
    "slack": "slackapi/slack-github-action@v2 with a webhook secret",
    "github-release": "softprops/action-gh-release@v2",
}

_DOCKER = {"plugin-docker-buildx", "docker", "plugin-docker"}
_GIT = {"plugin-git", "git"}


def matches(key) -> bool:
    return key == "settings"


def apply(key, value, step, ctx, report) -> None:
    image = ctx.step_image or "?"
    base = image.split(":")[0].split("/")[-1]
    settings = {}
    if isinstance(value, dict):
        for name, spec in value.items():
            settings[str(name)] = _secret(spec)

    if base in _GIT:
        step["_skip"] = True
        report.mapped(META.id, f"plugin: {image}", "dropped — actions/checkout is already the first step")
        return
    if base in _DOCKER:
        _docker(settings, step, report, image=image)
        return

    hint = _HINTS.get(base, "no direct equivalent — search the GitHub Marketplace for this plugin")
    report.manual(META.id, f"plugin: {image}",
                  hint + (f"; its settings were {sorted(settings)}" if settings else ""))
    step["run"] = f"echo 'TODO: port Woodpecker plugin {image} — {hint}'\n"
    if settings:
        env = step.setdefault("env", {})
        env.update({f"PLUGIN_{k.upper()}": v for k, v in settings.items()})


def _docker(settings: dict, step, report, *, image: str) -> None:
    repo = settings.get("repo")
    tags = settings.get("tags") or settings.get("tag") or "latest"
    tag_list = ([str(t) for t in tags] if isinstance(tags, list)
                else [t.strip() for t in str(tags).split(",") if t.strip()])
    references = [f"{repo}:{t}" for t in tag_list] if repo else []

    with_: dict = {"push": not settings.get("dry_run", False)}
    if references:
        with_["tags"] = "\n".join(references) if len(references) > 1 else references[0]
    if settings.get("dockerfile"):
        with_["file"] = str(settings["dockerfile"])
    if settings.get("context"):
        with_["context"] = str(settings["context"])
    if settings.get("platforms"):
        platforms = settings["platforms"]
        with_["platforms"] = ",".join(str(p) for p in platforms) if isinstance(platforms, list) else str(platforms)
    step["uses"] = "docker/build-push-action@v6"
    step["with"] = with_
    if settings.get("username") or settings.get("password"):
        report.manual(META.id, f"plugin: {image} (registry login)",
                      "add a docker/login-action@v3 step before this one with the same "
                      "username/password secrets")
    report.mapped(META.id, f"plugin: {image}", "docker/build-push-action@v6")


def _secret(value):
    if isinstance(value, dict) and "from_secret" in value:
        return "${{ secrets.%s }}" % str(value["from_secret"]).upper()
    return value
