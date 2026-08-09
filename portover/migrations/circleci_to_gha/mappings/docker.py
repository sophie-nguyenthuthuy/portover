"""docker — a CircleCI Docker executor becomes a GHA job container/services."""

from portover.core import MappingMeta

SCOPE = "job"

META = MappingMeta(
    id="docker",
    directive="docker: [{image, environment, auth}]",
    title="Migrate a CircleCI Docker executor to GitHub Actions",
    before="""docker:
  - image: cimg/python:3.12
    environment:
      PIP_DISABLE_PIP_VERSION_CHECK: "1"
  - image: postgres:16
    environment:
      POSTGRES_PASSWORD: postgres""",
    after="""container: cimg/python:3.12
env:
  PIP_DISABLE_PIP_VERSION_CHECK: "1"
services:
  service-1:
    image: postgres:16
    env:
      POSTGRES_PASSWORD: postgres""",
    notes=(
        "The first CircleCI image is the primary container; later images become "
        "GHA service containers. CircleCI image aliases and service readiness checks "
        "do not translate exactly, so portover flags aliases and custom entrypoints."
    ),
    priority=10,
)


def matches(key) -> bool:
    return key == "docker"


def _image(item):
    if isinstance(item, str):
        return item, {}
    if isinstance(item, dict):
        return item.get("image"), item
    return None, {}


def apply(key, value, job, ctx, report) -> None:
    images = value if isinstance(value, list) else [value]
    if not images:
        return
    image, spec = _image(images[0])
    if image:
        job["container"] = str(image)
        if isinstance(spec.get("environment"), dict):
            job.setdefault("env", {}).update(spec["environment"])
        if spec.get("auth"):
            report.manual(META.id, f"docker image {image}: auth",
                          "move registry credentials to secrets and add container.credentials")
    for i, item in enumerate(images[1:], 1):
        image, spec = _image(item)
        if not image:
            continue
        service = {"image": str(image)}
        if isinstance(spec.get("environment"), dict):
            service["env"] = spec["environment"]
        if spec.get("command") or spec.get("entrypoint"):
            report.manual(META.id, f"service image {image}",
                          "translate command/entrypoint to service options or a startup step")
        alias = spec.get("name")
        if alias:
            report.manual(META.id, f"service image {image}: name {alias}",
                          "GHA service hostnames come from the services key; verify this generated name")
        job.setdefault("services", {})[f"service-{i}"] = service
        report.manual(META.id, f"service image {image}",
                      f"verify networking: this service is reachable as `service-{i}`, not necessarily localhost")
    report.mapped(META.id, "docker executor", f"container {image if len(images) == 1 else 'plus services'}")
