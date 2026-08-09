"""artifact_paths — files uploaded after the step."""

from portover.core import MappingMeta

SCOPE = "step"

META = MappingMeta(
    id="artifact-paths",
    directive="artifact_paths: dist/**",
    title="Migrate Buildkite artifact_paths to GitHub Actions",
    before="""- label: Build
  command: make build
  artifact_paths:
    - dist/**
    - coverage/*.xml""",
    after="""- uses: actions/upload-artifact@v4
  if: always()
  with:
    name: build
    path: |
      dist/**
      coverage/*.xml""",
    notes=(
        "Buildkite uploads these even when the step fails (which is the point "
        "for logs and coverage), so portover adds `if: always()` to match — "
        "without it a GHA step is skipped after a failure and you lose exactly "
        "the artifacts you wanted. Downloading is the other half: Buildkite "
        "steps pull artifacts with `buildkite-agent artifact download`, while "
        "GHA needs an explicit actions/download-artifact in the consuming job."
    ),
    priority=20,
)


def matches(key) -> bool:
    return key == "artifact_paths"


def apply(key, value, job, ctx, report) -> None:
    from portover.migrations.buildkite_to_gha import as_list, interpolate

    paths = [interpolate(str(p), ctx) for p in as_list(value)]
    if not paths:
        return
    name = ctx.current_jid or "artifacts"
    job.setdefault("_post_steps", []).append(
        {"uses": "actions/upload-artifact@v4", "if": "always()",
         "with": {"name": name, "path": "\n".join(paths) if len(paths) > 1 else paths[0]}})
    job.setdefault("_artifacts", []).append(name)
    report.mapped(META.id, f"artifact_paths: {paths}", f"upload-artifact '{name}' (if: always())")
