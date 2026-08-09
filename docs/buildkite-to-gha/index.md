# buildkite-to-gha: Buildkite pipeline.yml → .github/workflows/*.yml (GitHub Actions)

Run it: `portover run buildkite-to-gha <dir>` (dry run) then `--write`.

One page per directive:

- [`command: / commands:`](command.md) — Migrate Buildkite command steps to GitHub Actions run steps
- [`depends_on: key / [{step, allow_failure}]`](depends-on.md) — Migrate Buildkite depends_on to GitHub Actions needs
- [`env / agents / notify (pipeline level)`](pipeline-settings.md) — Migrate Buildkite pipeline-level settings to GitHub Actions
- [`if: / branches: / skip:`](conditions.md) — Migrate Buildkite if, branches and skip to GitHub Actions
- [`matrix: (list or setup/adjustments) / parallelism: N`](matrix.md) — Migrate Buildkite matrix and parallelism to GitHub Actions
- [`plugins: [org/name#v1.0.0: {config}]`](plugins.md) — Migrate Buildkite plugins to GitHub Actions
- [`artifact_paths: dist/**`](artifact-paths.md) — Migrate Buildkite artifact_paths to GitHub Actions
- [`agents: {queue: default, os: linux}`](agents.md) — Migrate Buildkite agents to GitHub Actions runs-on
- [`env / timeout_in_minutes / soft_fail / retry / concurrency / priority`](step-settings.md) — Migrate the remaining Buildkite step settings to GitHub Actions
- [`steps: [command / wait / block / input / trigger / group]`](steps.md) — Migrate Buildkite steps to GitHub Actions jobs
- [`- wait / - wait: {continue_on_failure: true}`](wait.md) — Migrate Buildkite wait steps to GitHub Actions needs
- [`- group: name / steps / depends_on`](group.md) — Migrate Buildkite group steps to GitHub Actions
- [`- block: / - input: with fields / prompt`](block-input.md) — Migrate Buildkite block and input steps to GitHub Actions
- [`- trigger: other-pipeline / build / async`](trigger.md) — Migrate Buildkite trigger steps to GitHub Actions
- [`$BUILDKITE_COMMIT, $BUILDKITE_BRANCH, buildkite-agent ...`](variables.md) — Migrate Buildkite variables and the buildkite-agent CLI to GitHub Actions
