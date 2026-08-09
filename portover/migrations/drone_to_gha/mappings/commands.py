"""commands — what a step runs."""

from portover.core import MappingMeta

SCOPE = "step"

META = MappingMeta(
    id="commands",
    directive="commands: [...]",
    title="Migrate Drone commands to GitHub Actions run steps",
    before="""- name: test
  image: golang:1.22
  commands:
    - go vet ./...
    - go test ./...""",
    after="""- name: test
  run: |
    go vet ./...
    go test ./...

# when the step's image differs from the rest of the pipeline:
- name: test
  run: |
    docker run --rm -i \\
      -v "$PWD":/drone/src -w /drone/src golang:1.22 sh -e <<'DRONE_STEP'
    go vet ./...
    go test ./...
    DRONE_STEP""",
    notes=(
        "Drone runs a step's commands with `set -e` in one shell, so the whole "
        "list becomes a single `run:` block rather than one step per line — "
        "that keeps `cd` and exported variables working across the lines, which "
        "splitting would break. The `docker run` form appears only when the "
        "pipeline's steps use different images; it bind-mounts the workspace "
        "so the files a previous step wrote are still there, and forwards the "
        "step's environment with -e."
    ),
    priority=10,
)


def matches(key) -> bool:
    return key in ("commands", "command")


def apply(key, value, step, ctx, report) -> None:
    from portover.migrations.drone_to_gha import WORKSPACE, as_list, note_vars

    commands = [str(c) for c in as_list(value)]
    if not commands:
        return
    for command in commands:
        note_vars(command, ctx)
    body = "\n".join(commands)

    if getattr(ctx, "step_shared_image", True) or not getattr(ctx, "step_image", ""):
        step["run"] = body + "\n"
        report.mapped(META.id, f"commands: {len(commands)}")
        return

    forwarded = "".join(f" -e {name}" for name in sorted(getattr(ctx, "step_env", {}) or {}))
    step["run"] = (
        f'docker run --rm -i{forwarded} -v "$PWD":{WORKSPACE} -w {WORKSPACE} '
        f"{ctx.step_image} sh -e <<'DRONE_STEP'\n{body}\nDRONE_STEP\n"
    )
    report.mapped(META.id, f"commands: {len(commands)}", f"docker run {ctx.step_image}")
