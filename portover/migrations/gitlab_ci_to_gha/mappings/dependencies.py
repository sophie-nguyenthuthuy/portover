"""dependencies — which jobs' artifacts to download."""

from portover.core import MappingMeta

SCOPE = "job"

META = MappingMeta(
    id="dependencies",
    directive="dependencies: [build]",
    title="Migrate GitLab CI dependencies to GitHub Actions",
    before="dependencies:\n  - build",
    after="""- uses: actions/download-artifact@v4
  with:
    name: build""",
    notes=(
        "This is the directive people forget, and the resulting failure is "
        "confusing. GitLab passes artifacts from earlier stages *automatically*; "
        "`dependencies:` only narrows that set. GHA passes nothing between jobs "
        "— they run on different machines with fresh workspaces — so every "
        "artifact must be uploaded by the producer and downloaded by the "
        "consumer. portover adds the download step here, but a job that relied "
        "on the implicit pass-through (no `dependencies:` key at all) will need "
        "one added by hand. `dependencies: []` means 'download nothing', which "
        "is already the GHA default."
    ),
    priority=44,
)


def matches(key) -> bool:
    return key == "dependencies"


def apply(key, value, job, ctx, report) -> None:
    from portover.migrations.gitlab_ci_to_gha import as_list, slug

    names = [str(n) for n in as_list(value)]
    if not names:
        report.mapped(META.id, "dependencies: []", "download nothing — already the GHA default")
        return
    for name in names:
        job.setdefault("_pre_steps", []).append(
            {"uses": "actions/download-artifact@v4", "with": {"name": slug(name)}})
        report.mapped(META.id, f"dependencies: {name}", f"download-artifact '{slug(name)}'")
    report.manual(META.id, f"dependencies: {names}",
                  "confirm each named job actually uploads an artifact under that name — "
                  "GHA has no implicit artifact pass-through")
