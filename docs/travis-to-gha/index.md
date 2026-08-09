# travis-to-gha: .travis.yml (Travis CI) → .github/workflows/*.yml (GitHub Actions)

Run it: `portover run travis-to-gha <dir>` (dry run) then `--write`.

One page per directive:

- [`language / python / node_js / go`](language.md) — Migrate Travis language and version matrix to GitHub Actions
- [`env / env.global / env.jobs (secure: ...)`](env.md) — Migrate Travis env to GitHub Actions
- [`os / dist / arch`](os-dist.md) — Migrate Travis os and dist to GitHub Actions runs-on
- [`branches: only / except`](branches.md) — Migrate Travis branches to GitHub Actions on.push.branches
- [`cache: pip / npm / directories`](cache.md) — Migrate Travis cache to GitHub Actions
- [`services: postgresql / redis / mysql / docker ...`](services.md) — Migrate Travis services to GitHub Actions service containers
- [`addons: apt / chrome / firefox / ...`](addons.md) — Migrate Travis addons to GitHub Actions
- [`git: depth / submodules / lfs_skip_smudge`](git.md) — Migrate Travis git options to GitHub Actions checkout
- [`before_install / install / script / after_success / after_failure ...`](scripts.md) — Migrate Travis build phases to GitHub Actions steps
- [`jobs/matrix: include / exclude / allow_failures / fast_finish`](matrix-jobs.md) — Migrate Travis jobs and matrix customization to GitHub Actions
- [`deploy: provider: pypi / pages / script / releases ...`](deploy.md) — Migrate Travis deploy to GitHub Actions
- [`notifications: email / slack / ...`](notifications.md) — Migrate Travis notifications to GitHub Actions
