"""failure / detach / privileged / volumes / depends_on / resources — smaller step fields."""

from portover.core import MappingMeta

SCOPE = "step"

META = MappingMeta(
    id="step-settings",
    directive="failure / detach / privileged / volumes / depends_on / resources",
    title="Migrate the remaining Drone step settings to GitHub Actions",
    before="""- name: lint
  image: golangci/golangci-lint
  failure: ignore
  commands: [golangci-lint run]

- name: proxy
  image: nginx
  detach: true""",
    after="""- name: lint
  continue-on-error: true
  run: golangci-lint run

# detach has no equivalent — start it in the background:
- run: docker run -d --name proxy nginx""",
    notes=(
        "`failure: ignore` is `continue-on-error: true`. `detach: true` starts "
        "a long-running step alongside the others, which is what GHA service "
        "containers do — moving it to `services:` is usually the right answer, "
        "so it is flagged rather than translated blindly. `privileged`, "
        "`volumes` and `resources` all describe the Docker runner's sandbox and "
        "have no counterpart: GHA jobs get a whole VM, so privileged work "
        "generally just works, host volumes do not exist, and CPU/memory "
        "limits are fixed by the runner size."
    ),
    priority=20,
)


def matches(key) -> bool:
    return key in ("failure", "detach", "privileged", "volumes", "depends_on",
                   "resources", "network_mode", "dns", "user", "entrypoint", "group")


def apply(key, value, step, ctx, report) -> None:
    if key == "failure":
        if str(value) == "ignore":
            step["continue-on-error"] = True
            report.mapped(META.id, "failure: ignore", "continue-on-error: true")
        return
    if key == "detach":
        if value:
            report.manual(META.id, "detach: true",
                          "a background step — move it to the job's `services:` (that is what GHA "
                          "service containers are), or start it with `docker run -d` in a run step")
        return
    if key == "privileged":
        report.mapped(META.id, f"privileged: {value}",
                      "dropped — a GHA job runs on its own VM, so privileged work generally just works")
        return
    if key == "volumes":
        report.manual(META.id, "step volumes",
                      "no volume mounts in GHA — host paths do not exist, and the workspace is "
                      "already shared between steps")
        return
    if key == "depends_on":
        return  # handled by the steps mapping, which reports the DAG flattening
    if key == "resources":
        report.manual(META.id, "resources (cpu/memory limits)",
                      "no per-job resource limits — pick a larger runner if the job needs more")
        return
    if key in ("network_mode", "dns", "user", "entrypoint", "group"):
        report.manual(META.id, f"{key}: {value}",
                      "a Docker runner setting with no GHA counterpart — drop it or fold it into "
                      "the command")
