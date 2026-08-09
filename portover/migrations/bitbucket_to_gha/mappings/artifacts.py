"""artifacts — files handed to later steps."""

from portover.core import MappingMeta

SCOPE = "step"

META = MappingMeta(
    id="artifacts",
    directive="artifacts: [dist/**] / artifacts: {paths, download}",
    title="Migrate Bitbucket Pipelines artifacts to GitHub Actions",
    before="""- step:
    name: Build
    script: [make build]
    artifacts:
      - dist/**
- step:
    name: Deploy
    script: [./deploy.sh]     # dist/ is simply there""",
    after="""build:
  steps:
    - run: make build
    - uses: actions/upload-artifact@v4
      with: {name: build, path: dist/**}
deploy:
  needs: build
  steps:
    - uses: actions/download-artifact@v4   # added: GHA never passes files on
      with: {name: build}
    - run: ./deploy.sh""",
    notes=(
        "This is the difference that silently breaks migrated pipelines. "
        "Bitbucket gives every LATER step the artifacts of every earlier one, "
        "with no declaration at the consuming end — GHA jobs share nothing. So "
        "portover uploads at the producer and inserts the matching "
        "download-artifact in each subsequent job, reproducing the implicit "
        "behaviour. `download: false` on a step opts out of receiving them, "
        "which is the GHA default anyway."
    ),
    priority=20,
)


def matches(key) -> bool:
    return key == "artifacts"


def apply(key, value, job, ctx, report) -> None:
    from portover.migrations.bitbucket_to_gha import as_list

    paths = []
    if isinstance(value, dict):
        paths = [str(p) for p in as_list(value.get("paths"))]
        if value.get("download") is False:
            job["_no_download"] = True
            report.mapped(META.id, "artifacts.download: false",
                          "opted out of receiving earlier artifacts — already the GHA default")
    else:
        paths = [str(p) for p in as_list(value)]
    if not paths:
        return
    name = ctx.current_jid or "artifacts"
    job.setdefault("_post_steps", []).append(
        {"uses": "actions/upload-artifact@v4",
         "with": {"name": name, "path": "\n".join(paths) if len(paths) > 1 else paths[0]}})
    job.setdefault("_artifacts", []).append(name)
    report.mapped(META.id, f"artifacts: {paths}",
                  f"upload as '{name}' + download in every later job")
