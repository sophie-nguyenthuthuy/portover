"""image — the container a step runs in (top level or per step)."""

from portover.core import MappingMeta

SCOPE = "step"

META = MappingMeta(
    id="image",
    directive="image: name / image: {name, username, password}",
    title="Migrate Bitbucket Pipelines image to GitHub Actions container",
    before="""image:
  name: private.registry/build:1.2
  username: $REGISTRY_USER
  password: $REGISTRY_PASS""",
    after="""container:
  image: private.registry/build:1.2
  credentials:
    username: ${{ secrets.REGISTRY_USER }}
    password: ${{ secrets.REGISTRY_PASS }}""",
    notes=(
        "Every Bitbucket step runs in a container, so `image:` is mandatory "
        "there and optional in GHA — which means the better migration is often "
        "to drop the container and use `runs-on: ubuntu-latest` with a setup "
        "action, since that gets you caching and preinstalled tooling. Keep the "
        "container when the image carries tools you need. Registry credentials "
        "map onto `container.credentials`, and the `$VAR` references become "
        "GitHub secrets. `run-as-user` maps to `container.options: --user N`."
    ),
    priority=12,
)


def matches(key) -> bool:
    return key == "image"


def apply(key, value, job, ctx, report) -> None:
    if isinstance(value, dict):
        name = value.get("name")
        if not name:
            return
        container: dict = {"image": str(name)}
        credentials = {k: _secret(value[k]) for k in ("username", "password") if value.get(k)}
        if credentials:
            container["credentials"] = credentials
            report.manual(META.id, "image credentials",
                          "create GitHub secrets for the registry username/password "
                          "(they were Bitbucket repository variables)")
        if value.get("run-as-user"):
            container["options"] = f"--user {value['run-as-user']}"
        if value.get("aws"):
            report.manual(META.id, "image.aws (ECR)",
                          "use aws-actions/amazon-ecr-login before the job, or a container registry secret")
        job["container"] = container if len(container) > 1 else container["image"]
    else:
        job["container"] = str(value)
    report.mapped(META.id, f"image: {value if not isinstance(value, dict) else value.get('name')}", "container:")


def _secret(value):
    text = str(value)
    if text.startswith("$") and text[1:].strip("{}").isidentifier():
        return "${{ secrets.%s }}" % text.strip("${}")
    return value
