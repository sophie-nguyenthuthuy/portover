"""default — pipeline-wide job defaults (and their legacy top-level spellings)."""

from portover.core import MappingMeta

SCOPE = "pipeline"

META = MappingMeta(
    id="defaults",
    directive="default: / top-level image, services, before_script, after_script, cache",
    title="Migrate the GitLab CI default block to GitHub Actions",
    before="""default:
  image: python:3.12
  before_script:
    - pip install -r requirements.txt""",
    after="""jobs:
  test:
    container: python:3.12
    steps:
      - uses: actions/checkout@v4
      - run: pip install -r requirements.txt   # copied into every job
      - run: pytest -q""",
    notes=(
        "GHA has no pipeline-wide job defaults, so portover copies each default "
        "into every job it applies to — a job that sets its own `image:` or "
        "`before_script:` overrides it, exactly like GitLab. The one GHA default "
        "that does exist is `defaults.run` (shell and working-directory), which "
        "is per-workflow. Top-level `image:`/`services:`/`cache:`/`before_script:` "
        "are the older spelling of the same thing and are treated identically."
    ),
    priority=14,
)

_INHERITABLE = ("image", "services", "before_script", "after_script", "cache",
                "tags", "retry", "timeout", "interruptible", "artifacts")


def matches(key) -> bool:
    return key == "default" or key in ("image", "services", "before_script", "after_script", "cache")


def apply(key, value, ctx, report) -> None:
    if key == "default":
        if not isinstance(value, dict):
            return
        for name, spec in value.items():
            if name in _INHERITABLE:
                ctx.defaults[name] = spec
                report.mapped(META.id, f"default.{name}", "applied to every job")
            else:
                report.manual(META.id, f"default.{name}", "no pipeline-wide equivalent — set it per job")
        return
    ctx.defaults[key] = value
    report.mapped(META.id, f"{key}: (top-level)", f"treated as default.{key} for every job")
