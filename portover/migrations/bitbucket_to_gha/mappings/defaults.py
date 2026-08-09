"""Top-level image / clone / options — defaults for every step."""

from portover.core import MappingMeta

SCOPE = "pipeline"

META = MappingMeta(
    id="defaults",
    directive="image / clone / options (top level)",
    title="Migrate Bitbucket Pipelines global settings to GitHub Actions",
    before="""image: python:3.12

clone:
  depth: full
  lfs: true

options:
  max-time: 30""",
    after="""jobs:
  build:
    container: python:3.12          # copied into every job
    timeout-minutes: 30
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0           # depth: full
          lfs: true""",
    notes=(
        "GHA has no pipeline-wide job defaults, so each of these is copied into "
        "every job, and a step that sets its own value wins — the same "
        "precedence Bitbucket uses. `clone.depth: full` is `fetch-depth: 0`, "
        "and a numeric depth maps straight across (Bitbucket defaults to 50, "
        "GHA to 1, so a script running `git log` or `git describe` may need "
        "this set explicitly). `clone.enabled: false` means no checkout at all."
    ),
    priority=14,
)


def matches(key) -> bool:
    return key in ("image", "clone", "options")


def apply(key, value, ctx, report) -> None:
    if key == "image":
        ctx.default_image = value
        report.mapped(META.id, "image (global)", "container: on every job")
        return
    if key == "clone":
        ctx.clone = value if isinstance(value, dict) else {}
        report.mapped(META.id, "clone (global)", "checkout options on every job")
        return
    if not isinstance(value, dict):
        return
    ctx.options = value
    if value.get("max-time"):
        report.mapped(META.id, f"options.max-time: {value['max-time']}", "timeout-minutes on every job")
    if value.get("size"):
        report.manual(META.id, f"options.size: {value['size']}",
                      "step size maps to a larger GitHub-hosted runner label your org configures")
    if value.get("docker"):
        report.mapped(META.id, "options.docker", "dropped — the docker daemon is available on GHA runners")
