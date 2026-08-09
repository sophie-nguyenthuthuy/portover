"""portover CLI: list, detect, run, docs."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from portover import __version__
from portover.migrations import REGISTRY, get


def cmd_list(_args) -> int:
    width = max(len(m.id) for m in REGISTRY)
    for m in REGISTRY:
        print(f"  {m.id:<{width}}  {m.source} -> {m.target}")
    return 0


def cmd_detect(args) -> int:
    root = Path(args.path)
    hits = [(m, m.detect(root)) for m in REGISTRY]
    hits = [(m, files) for m, files in hits if files]
    if not hits:
        print(f"nothing to migrate in {root.resolve()}")
        return 1
    for m, files in hits:
        print(f"  {m.id}: {', '.join(files)}")
    print(f"\nrun one with: portover run <id> {args.path}")
    return 0


def print_report(report, write: bool, root: Path) -> None:
    counts = report.counts()
    if counts:
        width = max(len(k) for k in counts)
        for mid, (n, manual) in sorted(counts.items()):
            mark = "!" if manual else "+"
            print(f"  {mark} {mid:<{width}}  {n}x")
    manual_hits = [h for h in report.hits if h.manual]
    if manual_hits:
        print("\nManual steps:")
        seen: dict = {}  # identical advice repeated per job is one instruction, not N
        for h in manual_hits:
            seen[(h.mapping_id, h.source, h.detail)] = seen.get((h.mapping_id, h.source, h.detail), 0) + 1
        for (mapping_id, source, detail), count in seen.items():
            times = f" (x{count})" if count > 1 else ""
            print(f"  ! [{mapping_id}] {source}{times}")
            print(f"      {detail}")
    if report.unmapped:
        print("\nUnmapped (no mapping claims these — contribute one!):")
        for u in report.unmapped:
            print(f"  ? {u}")
    for rel, content in report.outputs.items():
        target = root / rel
        if write:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
            print(f"\nwrote {target}")
        else:
            print(f"\n--- {rel} (dry run; pass --write to save) ---")
            print(content)


def cmd_run(args) -> int:
    root = Path(args.path)
    try:
        migration = get(args.migration)
    except KeyError:
        print(f"unknown migration '{args.migration}' — try: portover list", file=sys.stderr)
        return 2
    if not migration.detect(root):
        print(f"{migration.id}: no {migration.source} files found in {root.resolve()}", file=sys.stderr)
        return 1
    print(f"== {migration.id}: {migration.source} -> {migration.target}\n")
    report = migration.run(root)
    print_report(report, args.write, root)
    return 0


def cmd_docs(args) -> int:
    from portover.docsgen import generate

    n = generate(Path(args.out))
    print(f"generated {n} pages under {args.out}/")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="portover", description="Migrate one config dialect to another, one directive at a time.")
    p.add_argument("--version", action="version", version=__version__)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list", help="list available migrations").set_defaults(fn=cmd_list)
    d = sub.add_parser("detect", help="show which migrations apply to a directory")
    d.add_argument("path", nargs="?", default=".")
    d.set_defaults(fn=cmd_detect)
    r = sub.add_parser("run", help="run a migration")
    r.add_argument("migration")
    r.add_argument("path", nargs="?", default=".")
    r.add_argument("--write", action="store_true", help="write output files (default: dry run)")
    r.set_defaults(fn=cmd_run)
    g = sub.add_parser("docs", help="generate one doc page per mapping")
    g.add_argument("--out", default="docs")
    g.set_defaults(fn=cmd_docs)
    args = p.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
