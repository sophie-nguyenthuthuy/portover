"""Generate one Markdown page per mapping.

Each page answers exactly one search: "how do I migrate <directive> from
<source> to <target>". That page-per-directive shape is the point — it is what
someone pastes into a search engine at 2am mid-migration.
"""

from __future__ import annotations

from pathlib import Path

from portover.migrations import REGISTRY

_LANG = {"pip-to-uv": ("text", "toml"), "jenkins-to-gha": ("groovy", "yaml"),
         "travis-to-gha": ("yaml", "yaml"), "gitlab-ci-to-gha": ("yaml", "yaml"), "circleci-to-gha": ("yaml", "yaml"), "azure-pipelines-to-gha": ("yaml", "yaml"), "bitbucket-to-gha": ("yaml", "yaml"), "buildkite-to-gha": ("yaml", "yaml"), "drone-to-gha": ("yaml", "yaml"), "woodpecker-to-gha": ("yaml", "yaml"),
         "flake8-to-ruff": ("ini", "toml")}


def mapping_page(migration, meta) -> str:
    before_lang, after_lang = _LANG.get(migration.id, ("text", "text"))
    lines = [
        f"# {meta.title}",
        "",
        f"**Directive:** `{meta.directive}`",
        "",
        f"Part of the [{migration.id}](index.md) migration — `portover run {migration.id}` applies this "
        "mapping (and every other one on this page's index) automatically.",
        "",
        f"## Before — {migration.source}",
        "",
        f"```{before_lang}",
        meta.before,
        "```",
        "",
        f"## After — {migration.target}",
        "",
        f"```{after_lang}",
        meta.after,
        "```",
    ]
    if meta.notes:
        lines += ["", "## What to watch for", "", meta.notes]
    lines += ["", "---", "", "*Wrong or incomplete? This page is generated from one small file — "
              f"[`mappings/{meta.id.replace('-', '_')}.py`](https://github.com/sophie-nguyenthuthuy/portover) — fix it there.*"]
    return "\n".join(lines) + "\n"


def index_page(migration, metas) -> str:
    lines = [
        f"# {migration.id}: {migration.source} → {migration.target}",
        "",
        f"Run it: `portover run {migration.id} <dir>` (dry run) then `--write`.",
        "",
        "One page per directive:",
        "",
    ]
    for meta in metas:
        lines.append(f"- [`{meta.directive}`]({meta.id}.md) — {meta.title}")
    return "\n".join(lines) + "\n"


def generate(out: Path) -> int:
    n = 0
    top = ["# portover docs", "", "One page per directive mapping, grouped by migration.", ""]
    for migration in REGISTRY:
        metas = [m.META for m in migration.mappings()]
        mdir = out / migration.id
        mdir.mkdir(parents=True, exist_ok=True)
        (mdir / "index.md").write_text(index_page(migration, metas))
        n += 1
        for meta in metas:
            (mdir / f"{meta.id}.md").write_text(mapping_page(migration, meta))
            n += 1
        top.append(f"- [{migration.id}]({migration.id}/index.md) — {migration.source} → {migration.target} ({len(metas)} mappings)")
    (out / "index.md").write_text("\n".join(top) + "\n")
    return n + 1
