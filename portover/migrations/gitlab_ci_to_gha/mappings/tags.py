"""tags — runner selection."""

from portover.core import MappingMeta

SCOPE = "job"

META = MappingMeta(
    id="tags",
    directive="tags: [docker, linux]",
    title="Migrate GitLab CI runner tags to GitHub Actions runs-on",
    before="tags:\n  - docker\n  - linux",
    after="runs-on: [self-hosted, docker, linux]",
    notes=(
        "Both systems pick a runner by label, so tags become `runs-on` labels. "
        "The catch is that a GitLab tag usually names a runner YOU registered, "
        "which means the honest translation is a self-hosted runner with the "
        "same labels — portover adds `self-hosted` for that reason. If the tag "
        "was only picking a size or an OS on GitLab's shared fleet "
        "(saas-linux-medium-amd64 and friends), replace it with the matching "
        "GitHub-hosted label (ubuntu-latest, or a larger runner your org has "
        "configured) instead."
    ),
    priority=32,
)

_HOSTED = {"linux": "ubuntu-latest", "ubuntu": "ubuntu-latest",
           "macos": "macos-latest", "osx": "macos-latest", "windows": "windows-latest"}


def matches(key) -> bool:
    return key == "tags"


def apply(key, value, job, ctx, report) -> None:
    from portover.migrations.gitlab_ci_to_gha import as_list

    labels = [str(t) for t in as_list(value)]
    if not labels:
        return
    if len(labels) == 1 and labels[0].lower() in _HOSTED:
        job["runs-on"] = _HOSTED[labels[0].lower()]
        report.mapped(META.id, f"tags: {labels}", f"runs-on: {job['runs-on']}")
        return
    if any(t.startswith("saas-") for t in labels):
        report.manual(META.id, f"tags: {labels}",
                      "GitLab SaaS runner tags — replace with a GitHub-hosted label (ubuntu-latest or a larger runner)")
    job["runs-on"] = ["self-hosted", *labels]
    report.mapped(META.id, f"tags: {labels}", f"runs-on: {job['runs-on']}")
