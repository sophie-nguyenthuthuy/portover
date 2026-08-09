# pip-to-uv: requirements.txt (pip) → pyproject.toml (uv)

Run it: `portover run pip-to-uv <dir>` (dry run) then `--write`.

One page per directive:

- [`-e / --editable`](editable.md) — Migrate pip -e (editable installs) to uv
- [`-r file / -c file`](include.md) — Migrate pip -r includes and -c constraints to uv
- [`--index-url / --extra-index-url`](index-url.md) — Migrate pip --index-url and --extra-index-url to uv
- [`--find-links / -f`](find-links.md) — Migrate pip --find-links to uv
- [`--pre / --no-binary / --only-binary`](option-flags.md) — Migrate pip --pre, --no-binary and --only-binary to uv
- [`pkg==1.2 --hash=sha256:...`](hashes.md) — Migrate pip --hash pinned requirements to uv
- [`git+https://... (VCS requirement)`](vcs.md) — Migrate pip git+https requirements to uv
- [`./local/pkg or wheel/sdist path`](local-path.md) — Migrate pip local path requirements to uv
- [`pkg==1.2, pkg[extra]>=2, pkg; python_version<"3.11"`](requirement.md) — Migrate plain requirements.txt lines to uv
