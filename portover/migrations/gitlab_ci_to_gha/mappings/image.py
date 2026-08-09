"""image — the container a job runs in."""

from portover.core import MappingMeta

SCOPE = "job"

META = MappingMeta(
    id="image",
    directive="image: name / image: {name, entrypoint}",
    title="Migrate GitLab CI image to GitHub Actions container",
    before="image: python:3.12",
    after="""runs-on: ubuntu-latest
container: python:3.12""",
    notes=(
        "GitLab runs every job in a container by default; GHA runs on the "
        "runner VM unless you ask for one, so `image:` becomes `container:` on "
        "top of `runs-on:`. Often the better migration is to drop the container "
        "entirely and use a setup action (`actions/setup-python@v5`) — that is "
        "faster and gives you dependency caching. Keep the container when the "
        "image carries tools you actually need. `entrypoint: [\"\"]` is a GitLab "
        "workaround for images with an entrypoint and has no GHA counterpart: "
        "container steps override the entrypoint already."
    ),
    priority=12,
)


def matches(key) -> bool:
    return key == "image"


def apply(key, value, job, ctx, report) -> None:
    if isinstance(value, dict):
        name = value.get("name")
        container: dict = {"image": str(name)} if name else {}
        if value.get("entrypoint"):
            report.manual(META.id, f"image.entrypoint: {value['entrypoint']}",
                          "not needed — GHA container steps already override the image entrypoint")
        for extra in ("docker", "pull_policy"):
            if extra in value:
                report.manual(META.id, f"image.{extra}", "no GHA equivalent — configure it on the runner instead")
        job["container"] = container.get("image", "") or job.get("container", "")
        if not job["container"]:
            job.pop("container", None)
            return
    else:
        job["container"] = str(value)
    report.mapped(META.id, f"image: {job['container']}", "container:")
