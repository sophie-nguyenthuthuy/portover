"""restore_cache/save_cache — GitHub Actions cache steps."""

from portover.core import MappingMeta

SCOPE = "step"

META = MappingMeta(
    id="cache", directive="- restore_cache / save_cache", title="Migrate CircleCI caches",
    before="""- restore_cache:
    keys: [v1-deps-{{ checksum \"requirements.txt\" }}, v1-deps-]
- save_cache:
    key: v1-deps-{{ checksum \"requirements.txt\" }}
    paths: [.venv]""",
    after="""- uses: actions/cache@v4
  with:
    path: .venv
    key: v1-deps-${{ hashFiles('requirements.txt') }}
    restore-keys: v1-deps-""",
    notes="GHA combines restore and save in one action. A restore-only step has no path in CircleCI, so portover flags it for completion.",
    priority=30,
)


def matches(name) -> bool:
    return name in ("restore_cache", "save_cache")


def _key(value):
    import re
    s = str(value)
    s = re.sub(r'\{\{\s*checksum\s+["\']([^"\']+)["\']\s*\}\}', r"${{ hashFiles('\1') }}", s)
    s = s.replace("{{ arch }}", "${{ runner.arch }}").replace("{{ .Branch }}", "${{ github.ref_name }}")
    return s


def apply(name, value, out, ctx, report) -> None:
    spec = value if isinstance(value, dict) else {}
    if name == "restore_cache":
        keys = spec.get("keys", spec.get("key", []))
        keys = keys if isinstance(keys, list) else [keys]
        step = {"uses": "actions/cache/restore@v4", "with": {"path": ".cache", "key": _key(keys[0] if keys else "cache")}}
        if len(keys) > 1:
            step["with"]["restore-keys"] = "\n".join(_key(k) for k in keys[1:])
        out.append(step)
        report.manual(META.id, "restore_cache", "replace generated `.cache` path with the paths saved by the matching save_cache step")
    else:
        paths = spec.get("paths") or [".cache"]
        path = "\n".join(str(p) for p in paths) if isinstance(paths, list) else str(paths)
        out.append({"uses": "actions/cache/save@v4", "with": {"path": path, "key": _key(spec.get("key", "cache"))}})
        report.mapped(META.id, "save_cache", "actions/cache/save@v4")
