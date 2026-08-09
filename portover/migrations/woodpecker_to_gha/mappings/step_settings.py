"""image / failure / detach / directory / group / privileged / pull / backend_options."""

from portover.core import MappingMeta

SCOPE = "step"

META = MappingMeta(
    id="step-settings",
    directive="image / failure / detach / directory / group / privileged / pull",
    title="Migrate the remaining Woodpecker step settings to GitHub Actions",
    before="""- name: lint
  image: golangci/golangci-lint
  failure: ignore
  directory: backend
  commands: [golangci-lint run]""",
    after="""- name: lint
  continue-on-error: true
  working-directory: backend
  run: golangci-lint run""",
    notes=(
        "`failure: ignore` is `continue-on-error: true` and `directory:` is "
        "`working-directory:`. `detach: true` starts a long-running step "
        "alongside the others — GHA service containers are the equivalent, so "
        "moving it to `services:` is usually right and portover flags it "
        "rather than guessing. `group:` (concurrent steps) cannot be expressed "
        "with GHA steps at all, since those are strictly sequential. "
        "`privileged`, `pull` and `backend_options` describe the Woodpecker "
        "agent's sandbox and have no counterpart: a GHA job gets its own VM, "
        "and there is no image pull policy."
    ),
    priority=20,
)


def matches(key) -> bool:
    return key in ("image", "failure", "detach", "directory", "group", "privileged",
                   "pull", "backend_options", "depends_on", "volumes", "ports", "entrypoint")


def apply(key, value, step, ctx, report) -> None:
    if key == "image":
        return  # recorded by the steps mapping, which decides container vs docker run
    if key == "failure":
        if str(value) == "ignore":
            step["continue-on-error"] = True
            report.mapped(META.id, "failure: ignore", "continue-on-error: true")
        return
    if key == "directory":
        step["working-directory"] = str(value)
        report.mapped(META.id, f"directory: {value}", "working-directory")
        return
    if key == "detach":
        if value:
            report.manual(META.id, "detach: true",
                          "a background step — move it to the job's `services:` (that is what GHA "
                          "service containers are), or start it with `docker run -d` in a run step")
        return
    if key in ("group", "depends_on"):
        return  # reported once by the steps mapping
    if key == "privileged":
        report.mapped(META.id, f"privileged: {value}",
                      "dropped — a GHA job runs on its own VM, so privileged work generally just works")
        return
    if key == "pull":
        report.mapped(META.id, f"pull: {value}", "dropped — GHA has no image pull policy")
        return
    if key == "volumes":
        report.manual(META.id, "step volumes",
                      "no volume mounts in GHA — host paths do not exist, and the workspace is "
                      "already shared between steps")
        return
    if key == "ports":
        report.manual(META.id, f"ports: {value}",
                      "only service containers publish ports in GHA — move this step to `services:`")
        return
    if key in ("backend_options", "entrypoint"):
        report.manual(META.id, f"{key}",
                      "an agent/backend setting with no GHA counterpart — drop it or fold it "
                      "into the command")
