"""setup_remote_docker — unnecessary on GitHub-hosted Linux runners."""

from portover.core import MappingMeta

SCOPE = "step"

META = MappingMeta(
    id="setup-remote-docker", directive="- setup_remote_docker",
    title="Migrate CircleCI remote Docker setup",
    before="- setup_remote_docker", after="# remove it; Docker is already available on ubuntu runners",
    notes="If the job itself runs in a container, Docker access differs; use a host runner or a purpose-built build action.",
    priority=15,
)


def matches(name) -> bool:
    return name == "setup_remote_docker"


def apply(name, value, out, ctx, report) -> None:
    report.mapped(META.id, "setup_remote_docker", "dropped — Docker is preinstalled")
