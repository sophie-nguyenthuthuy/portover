"""VCS requirements (git+https://..., name @ git+...)."""

import re
from urllib.parse import urlparse

from portover.core import MappingMeta
from portover.migrations.pip_to_uv import req_name

META = MappingMeta(
    id="vcs",
    directive="git+https://... (VCS requirement)",
    title="Migrate pip git+https requirements to uv",
    before="git+https://github.com/psf/requests.git@v2.32.3#egg=requests",
    after="""dependencies = ["requests"]

[tool.uv.sources]
requests = { git = "https://github.com/psf/requests.git", rev = "v2.32.3" }""",
    notes=(
        "The name moves to [project] dependencies, the URL to [tool.uv.sources]. "
        "@ref becomes rev; #subdirectory= becomes subdirectory. Only git sources "
        "are supported by uv — hg/svn/bzr are flagged for manual handling."
    ),
    priority=30,
)

_VCS = re.compile(r"^(?:(?P<name>[A-Za-z0-9][A-Za-z0-9._-]*)\s*@\s*)?(?P<vcs>git|hg|svn|bzr)\+(?P<url>\S+)$")


def matches(line: str) -> bool:
    return bool(_VCS.match(line))


def apply(line: str, ctx, report) -> None:
    m = _VCS.match(line)
    if m.group("vcs") != "git":
        report.manual(META.id, line, f"uv has no {m.group('vcs')} support — vendor it or mirror to git")
        return
    url = m.group("url")
    frag = dict(p.split("=", 1) for p in urlparse(url).fragment.split("&") if "=" in p)
    url = url.split("#")[0]
    rev = None
    if "@" in url.split("://", 1)[-1]:
        url, _, rev = url.rpartition("@")
    name = m.group("name") or frag.get("egg") or req_name(url.rstrip("/").split("/")[-1].removesuffix(".git"))
    src = {"git": url}
    if rev:
        src["rev"] = rev
    if "subdirectory" in frag:
        src["subdirectory"] = frag["subdirectory"]
    (ctx.dev_deps if ctx.dev else ctx.deps).append(name)
    ctx.sources[name] = src
    report.mapped(META.id, line, f"{name} -> git source" + (f" @ {rev}" if rev else ""))
