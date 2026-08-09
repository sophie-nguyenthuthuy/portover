"""steps — the step list (or map), and the per-step image problem."""

from portover.core import MappingMeta

SCOPE = "pipeline"

META = MappingMeta(
    id="steps",
    directive="steps: (list or map) — also the older `pipeline:` key",
    title="Migrate Woodpecker steps to GitHub Actions",
    before="""steps:                        # list form
  - name: build
    image: golang:1.22
    commands: [go build]

steps:                        # map form — equally valid
  build:
    image: golang:1.22
    commands: [go build]""",
    after="""jobs:
  woodpecker:
    container: golang:1.22
    steps:
      - uses: actions/checkout@v4
      - name: build
        run: go build""",
    notes=(
        "Woodpecker accepts both spellings — a list where each entry carries "
        "`name:`, and a map keyed by step name — so portover normalises them "
        "before converting. Older configs use `pipeline:` instead of `steps:`, "
        "which is handled identically. Steps share the workspace volume, which "
        "is GHA step behaviour, so they become steps of one job rather than "
        "separate jobs. Per-step images are the mismatch: GHA containers are "
        "per job, so a shared image becomes `container:` while differing "
        "images run through `docker run` with the workspace bind-mounted."
    ),
    priority=40,
)


def matches(key) -> bool:
    return key in ("steps", "pipeline")


def apply(key, value, job, ctx, report) -> None:
    from portover.migrations.woodpecker_to_gha import interpolate_matrix, normalize_steps, scoped

    entries = normalize_steps(value, report)
    if not entries:
        return
    if key == "pipeline":
        report.manual(META.id, "pipeline:",
                      "`pipeline:` is the pre-1.0 spelling of `steps:` — rename it in the source config")

    command_images = [interpolate_matrix(str(s.get("image")), ctx) for s in entries
                      if s.get("image") and (s.get("commands") or s.get("command"))]
    shared = len(set(command_images)) <= 1
    if shared and command_images:
        job["container"] = command_images[0]
        report.mapped(META.id, f"image: {command_images[0]}", "job container (every step shares it)")
    elif command_images:
        report.manual(META.id, f"{len(set(command_images))} different step images",
                      "GHA containers are per job, so each step runs `docker run` with its own "
                      "image and the workspace bind-mounted — replace any image that only "
                      "supplied a toolchain with a setup-* action and a plain run step")

    if any(s.get("group") for s in entries):
        report.manual(META.id, "step group:",
                      "steps sharing a `group:` run concurrently in Woodpecker; GHA steps are "
                      "strictly sequential, so they are emitted in order — split them into "
                      "separate jobs if the parallelism mattered")
    if any(s.get("depends_on") for s in entries):
        report.manual(META.id, "step depends_on:",
                      "these steps form a DAG and could run concurrently; GHA steps run in "
                      "file order — split them into separate jobs if that matters")

    step_maps = scoped("step")
    out = job.setdefault("_steps", [])
    for entry in entries:
        step: dict = {}
        ctx.step_image = interpolate_matrix(str(entry.get("image") or ""), ctx)
        ctx.step_shared_image = shared
        ctx.step_env = {}
        for field_name, spec in entry.items():
            if field_name == "name":
                step["name"] = str(spec)
                continue
            for m in step_maps:
                if m.matches(field_name):
                    m.apply(field_name, spec, step, ctx, report)
                    break
            else:
                report.unmapped.append(f"step {entry.get('name', '?')}: {field_name}")
        if step.pop("_skip", False):
            continue
        if "run" in step or "uses" in step:
            out.append(step)
        else:
            report.manual(META.id, f"step: {entry.get('name', '?')}",
                          "no commands and no recognised plugin — add this step by hand")
