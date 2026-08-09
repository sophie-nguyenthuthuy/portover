"""run — shell commands."""

from portover.core import MappingMeta

SCOPE = "step"

META = MappingMeta(
    id="run", directive="- run: <command>", title="Migrate a CircleCI run step",
    before="""- run:
    name: Unit tests
    command: pytest -q
    no_output_timeout: 20m""",
    after="""- name: Unit tests
  run: pytest -q
  timeout-minutes: 20""",
    notes="CircleCI `when: always` becomes `if: always()`. Background processes and per-step environments need review.",
    priority=20,
)


def matches(name) -> bool:
    return name == "run"


def _minutes(value):
    s = str(value).strip()
    try:
        if s.endswith("h"):
            return int(float(s[:-1]) * 60)
        if s.endswith("m"):
            return int(float(s[:-1]))
        if s.endswith("s"):
            return max(1, int(float(s[:-1]) / 60))
    except ValueError:
        return None
    return None


def apply(name, value, out, ctx, report) -> None:
    from portover.migrations.circleci_to_gha import interpolate

    if isinstance(value, str):
        spec = {"command": value}
    elif isinstance(value, dict):
        spec = value
    else:
        report.unmapped.append(f"step run: {value!r}")
        return
    command = interpolate(spec.get("command", ""), ctx)
    step = {"run": command}
    if spec.get("name"):
        step = {"name": str(spec["name"]), **step}
    when = spec.get("when")
    if when == "always":
        step["if"] = "always()"
    elif when == "on_fail":
        step["if"] = "failure()"
    timeout = _minutes(spec.get("no_output_timeout")) if spec.get("no_output_timeout") else None
    if timeout:
        step["timeout-minutes"] = timeout
    if spec.get("working_directory"):
        step["working-directory"] = str(spec["working_directory"]).removeprefix("~/project/")
    if spec.get("environment"):
        if isinstance(spec["environment"], dict):
            step["env"] = spec["environment"]
        else:
            report.manual(META.id, f"run: {spec.get('name', command)} environment",
                          "expected an environment mapping; add this step's env values by hand")
    if spec.get("background"):
        command = command.rstrip() + " &"
        step["run"] = command
        report.manual(META.id, f"run: {spec.get('name', command)} background",
                      "verify the background process remains alive and ready for later steps")
    if not command:
        report.manual(META.id, "run step", "missing command")
    for option in set(spec) - {"command", "name", "when", "no_output_timeout", "working_directory",
                                    "environment", "background", "shell"}:
        report.unmapped.append(f"run step {spec.get('name', command)}: {option}")
    if spec.get("shell"):
        raw_shell = str(spec["shell"])
        if "{0}" in raw_shell:
            step["shell"] = raw_shell
        else:
            step["shell"] = raw_shell.split()[0].rsplit("/", 1)[-1]
            report.manual(META.id, f"run: {spec.get('name', command)} shell",
                          f"reduced `{raw_shell}` to `{step['shell']}` because GHA custom shell templates require `{{0}}`")
    out.append(step)
    report.mapped(META.id, f"run: {spec.get('name', command)}")
