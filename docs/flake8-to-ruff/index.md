# flake8-to-ruff: .flake8 / setup.cfg [flake8] → ruff.toml

Run it: `portover run flake8-to-ruff <dir>` (dry run) then `--write`.

One page per directive:

- [`max-line-length`](line-length.md) — Migrate flake8 max-line-length to ruff
- [`select / ignore / extend-select / extend-ignore`](select-ignore.md) — Migrate flake8 select and ignore lists to ruff
- [`exclude / extend-exclude`](exclude.md) — Migrate flake8 exclude to ruff
- [`per-file-ignores`](per-file-ignores.md) — Migrate flake8 per-file-ignores to ruff
- [`max-complexity`](mccabe.md) — Migrate flake8 max-complexity to ruff
