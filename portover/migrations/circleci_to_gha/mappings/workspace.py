"""CircleCI workspaces — artifact upload/download between jobs."""

from portover.core import MappingMeta

SCOPE = "step"

META = MappingMeta(
    id="workspace", directive="- persist_to_workspace / attach_workspace",
    title="Migrate CircleCI workspaces",
    before="""- persist_to_workspace:
    root: .
    paths: [dist]
- attach_workspace:
    at: .""",
    after="""- uses: actions/upload-artifact@v4
  with:
    name: workspace
    path: dist
- uses: actions/download-artifact@v4
  with:
    name: workspace
    path: .""",
    notes="Artifacts are the closest GHA equivalent. Artifact paths are rooted differently, so verify the download layout.",
    priority=30,
)


def matches(name) -> bool:
    return name in ("persist_to_workspace", "attach_workspace")


def apply(name, value, out, ctx, report) -> None:
    spec = value if isinstance(value, dict) else {}
    if name == "persist_to_workspace":
        paths = spec.get("paths") or ["."]
        paths = paths if isinstance(paths, list) else [paths]
        root = str(spec.get("root", ".")).rstrip("/")
        rooted = [str(p) if root in ("", ".") else f"{root}/{p}" for p in paths]
        path = "\n".join(rooted)
        out.append({"uses": "actions/upload-artifact@v4", "with": {"name": "workspace", "path": path}})
    else:
        out.append({"uses": "actions/download-artifact@v4", "with": {"name": "workspace", "path": spec.get("at", ".")}})
    report.mapped(META.id, name, "artifact action")
