"""os / dist / arch -> runs-on."""

from portover.core import MappingMeta

META = MappingMeta(
    id="os-dist",
    directive="os / dist / arch",
    title="Migrate Travis os and dist to GitHub Actions runs-on",
    before="os:\n  - linux\n  - osx\ndist: jammy",
    after="""strategy:
  matrix:
    os: [ubuntu-22.04, macos-latest]
runs-on: ${{ matrix.os }}""",
    notes=(
        "dist codenames pin the Ubuntu image (jammy -> ubuntu-22.04); EOL "
        "codenames fall back to ubuntu-latest with a flag. arm64/ppc64le/s390x "
        "arches need self-hosted or partner runners — flagged."
    ),
    priority=14,
)

_OS = {"linux": None, "osx": "macos-latest", "windows": "windows-latest", "freebsd": None}
_DIST = {"jammy": "ubuntu-22.04", "noble": "ubuntu-24.04", "focal": "ubuntu-20.04"}


def matches(key) -> bool:
    return key in ("os", "dist", "arch")


def _runner(name, ctx, report):
    if name == "linux":
        return ctx.runs_on if isinstance(ctx.runs_on, str) and ctx.runs_on.startswith("ubuntu") else "ubuntu-latest"
    runner = _OS.get(name)
    if runner is None:
        report.manual(META.id, f"os: {name}", f"no hosted runner for '{name}' — use ubuntu-latest or self-hosted")
        return "ubuntu-latest"
    return runner


def apply(key, value, ctx, report) -> None:
    if key == "arch":
        arches = value if isinstance(value, list) else [value]
        for a in arches:
            if str(a) not in ("amd64", "x86_64"):
                report.manual(META.id, f"arch: {a}", "non-x86 arch needs self-hosted/partner runners (or QEMU via docker/setup-qemu-action)")
        return
    if key == "dist":
        runner = _DIST.get(str(value))
        if runner is None:
            report.manual(META.id, f"dist: {value}", f"'{value}' has no current GHA image — using ubuntu-latest")
            runner = "ubuntu-latest"
        else:
            report.mapped(META.id, f"dist: {value}", f"runs-on: {runner}")
        if not ctx.matrix.get("os"):
            ctx.runs_on = runner
        return
    names = [str(v) for v in (value if isinstance(value, list) else [value])]
    if len(names) > 1:
        ctx.matrix["os"] = [_runner(n, ctx, report) for n in names]
        ctx.runs_on = "${{ matrix.os }}"
        report.mapped(META.id, f"os: {names}", "matrix.os")
    else:
        ctx.runs_on = _runner(names[0], ctx, report)
        report.mapped(META.id, f"os: {names[0]}", f"runs-on: {ctx.runs_on}")
