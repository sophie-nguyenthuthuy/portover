"""git — clone depth, submodules, lfs."""

from portover.core import MappingMeta

META = MappingMeta(
    id="git",
    directive="git: depth / submodules / lfs_skip_smudge",
    title="Migrate Travis git options to GitHub Actions checkout",
    before="git:\n  depth: false\n  submodules: true",
    after="""- uses: actions/checkout@v4
  with:
    fetch-depth: 0
    submodules: true""",
    notes=(
        "depth: false means full history -> fetch-depth: 0 (checkout's default "
        "is a shallow depth 1, same spirit as Travis' default 50). lfs_skip_smudge "
        "inverts into `lfs: true` on checkout when you DO want LFS files."
    ),
    priority=24,
)


def matches(key) -> bool:
    return key == "git"


def apply(key, value, ctx, report) -> None:
    if not isinstance(value, dict):
        return
    if "depth" in value:
        depth = value["depth"]
        ctx.fetch_depth = 0 if depth is False else int(depth)
        report.mapped(META.id, f"depth: {depth}", f"fetch-depth: {ctx.fetch_depth}")
    if value.get("submodules") is not None:
        report.manual(META.id, f"submodules: {value['submodules']}",
                      f"add `submodules: {str(bool(value['submodules'])).lower()}` to the checkout step's with:")
    if "lfs_skip_smudge" in value:
        report.manual(META.id, f"lfs_skip_smudge: {value['lfs_skip_smudge']}",
                      "checkout skips LFS by default; add `lfs: true` when you need the files")
