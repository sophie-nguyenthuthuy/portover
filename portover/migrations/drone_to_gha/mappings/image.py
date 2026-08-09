"""image / pull — the container a step runs in."""

from portover.core import MappingMeta

SCOPE = "step"

META = MappingMeta(
    id="image",
    directive="image: / pull:",
    title="Migrate the Drone step image to GitHub Actions",
    before="""- name: build
  image: golang:1.22
  pull: always""",
    after="""jobs:
  default:
    container: golang:1.22    # if every step shares it
    steps:
      - name: build
        run: go build""",
    notes=(
        "Where the image ends up is decided by the steps mapping (job "
        "`container:` when shared, `docker run` when not), so this mapping "
        "only records it. `pull: always|if-not-exists|never` has no GHA "
        "counterpart — GHA pulls when the image is absent and there is no "
        "policy knob — so it is dropped. An image from a private registry "
        "needs `container.credentials` or a docker/login-action step, which is "
        "flagged since the credentials cannot be inferred."
    ),
    priority=12,
)


def matches(key) -> bool:
    return key in ("image", "pull")


def apply(key, value, step, ctx, report) -> None:
    if key == "pull":
        report.mapped(META.id, f"pull: {value}", "dropped — GHA has no image pull policy")
        return
    image = str(value)
    if "/" in image and not image.startswith(("plugins/", "docker.io/")) and "." in image.split("/")[0]:
        report.manual(META.id, f"image: {image}",
                      "looks like a private registry — add docker/login-action (or container "
                      "credentials) before this step")
