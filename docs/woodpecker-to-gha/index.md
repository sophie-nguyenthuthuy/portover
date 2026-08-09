# woodpecker-to-gha: .woodpecker.yml (Woodpecker CI) → .github/workflows/*.yml (GitHub Actions)

Run it: `portover run woodpecker-to-gha <dir>` (dry run) then `--write`.

One page per directive:

- [`matrix: {VAR: [...], include: [...]}`](matrix.md) — Migrate Woodpecker matrix to GitHub Actions
- [`commands: [...]`](commands.md) — Migrate Woodpecker commands to GitHub Actions run steps
- [`clone / skip_clone / labels / platform / runs_on / variables`](workflow-settings.md) — Migrate Woodpecker workflow settings to GitHub Actions
- [`environment: (map or KEY=value list) / secrets: / from_secret`](environment.md) — Migrate Woodpecker environment and secrets to GitHub Actions
- [`when: [{event, branch, path, evaluate}]`](when.md) — Migrate Woodpecker when conditions to GitHub Actions if
- [`services: (map or list)`](services.md) — Migrate Woodpecker services to GitHub Actions service containers
- [`when: (on a step)`](step-when.md) — Migrate Woodpecker per-step when conditions to GitHub Actions
- [`settings: (a plugin step)`](settings.md) — Migrate Woodpecker plugins to GitHub Actions
- [`image / failure / detach / directory / group / privileged / pull`](step-settings.md) — Migrate the remaining Woodpecker step settings to GitHub Actions
- [`steps: (list or map) — also the older `pipeline:` key`](steps.md) — Migrate Woodpecker steps to GitHub Actions
- [`$CI_COMMIT_SHA, $CI_COMMIT_BRANCH, $CI_PIPELINE_NUMBER, ...`](ci-variables.md) — Migrate Woodpecker CI_ variables to GitHub Actions
