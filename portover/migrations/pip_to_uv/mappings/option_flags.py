"""Global resolver flags: --pre, --no-binary, --only-binary."""

from portover.core import MappingMeta

META = MappingMeta(
    id="option-flags",
    directive="--pre / --no-binary / --only-binary",
    title="Migrate pip --pre, --no-binary and --only-binary to uv",
    before="--pre\n--no-binary grpcio\n--only-binary numpy",
    after="""[tool.uv]
prerelease = "allow"
no-binary-package = ["grpcio"]
no-build-package = ["numpy"]""",
    notes=(
        "`--no-binary :all:` becomes `no-binary = true`; `--only-binary :all:` "
        "becomes `no-build = true`. Per-package lists map to the *-package keys."
    ),
    priority=12,
)


def matches(line: str) -> bool:
    return line.split("=")[0].split()[0] in ("--pre", "--no-binary", "--only-binary")


def _pkgs(line: str) -> list[str]:
    rest = line.replace("=", " ", 1).split(None, 1)
    return [p for p in rest[1].replace(",", " ").split()] if len(rest) > 1 else []


def apply(line: str, ctx, report) -> None:
    flag = line.replace("=", " ", 1).split()[0]
    if flag == "--pre":
        ctx.settings["prerelease"] = "allow"
        report.mapped(META.id, line, 'prerelease = "allow"')
        return
    key = "no-binary" if flag == "--no-binary" else "no-build"
    pkgs = _pkgs(line)
    if ":all:" in pkgs or not pkgs:
        ctx.settings[key] = True
        report.mapped(META.id, line, f"{key} = true")
    else:
        ctx.settings.setdefault(f"{key}-package", []).extend(pkgs)
        report.mapped(META.id, line, f"{key}-package += {pkgs}")
