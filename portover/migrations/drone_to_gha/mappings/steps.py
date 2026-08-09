"""steps — the pipeline's step list, and the per-step image problem."""

from portover.core import MappingMeta

SCOPE = "pipeline"

META = MappingMeta(
    id="steps",
    directive="steps: [{name, image, commands}]",
    title="Migrate Drone steps to GitHub Actions",
    before="""steps:
  - name: build
    image: golang:1.22
    commands:
      - go build
  - name: test
    image: golang:1.22
    commands:
      - go test ./...""",
    after="""jobs:
  default:
    container: golang:1.22      # every step shares one image
    steps:
      - uses: actions/checkout@v4
      - name: build
        run: go build
      - name: test
        run: go test ./...""",
    notes=(
        "Drone steps share the workspace volume, so files written by one step "
        "are simply there for the next — that is GHA's STEP behaviour, not its "
        "job behaviour, which is why a Drone pipeline becomes one job rather "
        "than one job per step. The catch is images: Drone names one per step, "
        "GHA has one per job. When every step uses the same image portover "
        "sets the job's `container:` and emits plain `run:` steps. When they "
        "differ it cannot use `container:` at all (a `docker run` inside a job "
        "container has no daemon), so each step runs `docker run` against its "
        "own image with the workspace bind-mounted — faithful, and the shared "
        "files still work. If an image was only supplying a toolchain, the "
        "cleaner migration is a setup-* action plus a plain `run:`."
    ),
    priority=40,
)


def matches(key) -> bool:
    return key == "steps"


def apply(key, value, job, ctx, report) -> None:
    from portover.migrations.drone_to_gha import as_list, scoped

    entries = [s for s in as_list(value) if isinstance(s, dict)]
    if not entries:
        return

    command_images = [str(s.get("image")) for s in entries
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

    step_maps = scoped("step")
    out = job.setdefault("_steps", [])
    ordered = _ordered(entries, report)
    for entry in ordered:
        step: dict = {}
        ctx.step_image = str(entry.get("image") or "")
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
        if "run" in step or "uses" in step:
            out.append(step)
        elif step.get("_skip"):
            step.pop("_skip")
        else:
            report.manual(META.id, f"step: {entry.get('name', '?')}",
                          "no commands and no recognised plugin — add this step by hand")


def _ordered(entries: list, report) -> list:
    """Drone steps are sequential unless depends_on makes them a DAG."""
    if not any(e.get("depends_on") for e in entries):
        return entries
    report.manual(META.id, "steps depends_on",
                  "these steps form a DAG in Drone and could run concurrently; GHA steps are "
                  "strictly sequential, so they are emitted in file order — split them into "
                  "separate jobs if the parallelism mattered")
    return entries
