"""commands — what a step runs."""

from portover.core import MappingMeta

SCOPE = "step"

META = MappingMeta(
    id="commands",
    directive="commands: [...]",
    title="Migrate Woodpecker commands to GitHub Actions run steps",
    before="""- name: test
  image: golang:1.22
  commands:
    - go vet ./...
    - go test ./...""",
    after="""- name: test
  run: |
    go vet ./...
    go test ./...""",
    notes=(
        "Woodpecker runs a step's commands in one shell with `set -e`, so the "
        "list becomes a single `run:` block rather than one step per line — "
        "that keeps `cd` and exported variables working across lines, which "
        "splitting would silently break. When the workflow's steps use "
        "different images the block instead runs `docker run` against that "
        "step's image, bind-mounting the workspace so files from earlier steps "
        "are still present, and forwarding the step's environment with -e."
    ),
    priority=12,
)


def matches(key) -> bool:
    return key in ("commands", "command")


def apply(key, value, step, ctx, report) -> None:
    from portover.migrations.woodpecker_to_gha import WORKSPACE, as_list, note_vars

    commands = [str(c) for c in as_list(value)]
    if not commands:
        return
    for command in commands:
        note_vars(command, ctx)
    body = "\n".join(commands)

    if ctx.step_shared_image or not ctx.step_image:
        step["run"] = body + "\n"
        report.mapped(META.id, f"commands: {len(commands)}")
        return

    forwarded = "".join(f" -e {name}" for name in sorted(ctx.step_env or {}))
    step["run"] = (
        f'docker run --rm -i{forwarded} -v "$PWD":{WORKSPACE} -w {WORKSPACE} '
        f"{ctx.step_image} sh -e <<'WOODPECKER_STEP'\n{body}\nWOODPECKER_STEP\n"
    )
    report.mapped(META.id, f"commands: {len(commands)}", f"docker run {ctx.step_image}")
