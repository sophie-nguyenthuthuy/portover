# circleci-to-gha: .circleci/config.yml (CircleCI) → .github/workflows/*.yml (GitHub Actions)

Run it: `portover run circleci-to-gha <dir>` (dry run) then `--write`.

One page per directive:

- [`executor: <name>`](executor.md) — Migrate a CircleCI reusable executor reference
- [`version: 2.1`](version.md) — Migrate the CircleCI config version key to GitHub Actions
- [`- checkout`](checkout.md) — Migrate the CircleCI checkout step
- [`docker: [{image, environment, auth}]`](docker.md) — Migrate a CircleCI Docker executor to GitHub Actions
- [`machine: {image: ...}`](machine.md) — Migrate a CircleCI machine executor
- [`macos: {xcode: ...}`](macos.md) — Migrate a CircleCI macOS executor
- [`parameters: (pipeline parameters)`](parameters.md) — Migrate CircleCI pipeline parameters to workflow_dispatch inputs
- [`orbs: name: namespace/orb@x.y`](orbs.md) — Migrate CircleCI orbs to GitHub Actions
- [`commands: (reusable commands)`](commands.md) — Migrate CircleCI reusable commands to GitHub Actions
- [`- setup_remote_docker`](setup-remote-docker.md) — Migrate CircleCI remote Docker setup
- [`executors: (reusable executors)`](executors.md) — Migrate CircleCI reusable executors to GitHub Actions
- [`jobs.<job>.environment`](job-environment.md) — Migrate CircleCI job environment variables
- [`jobs.<job>.parameters`](job-parameters.md) — Migrate CircleCI job parameters
- [`- run: <command>`](run.md) — Migrate a CircleCI run step
- [`shell: /bin/bash -eo pipefail`](shell.md) — Migrate the CircleCI job shell
- [`working_directory: path`](working-directory.md) — Migrate a CircleCI job working directory
- [`- store_artifacts / store_test_results`](artifacts.md) — Migrate CircleCI artifacts and test results
- [`- restore_cache / save_cache`](cache.md) — Migrate CircleCI caches
- [`parallelism: N`](parallelism.md) — Migrate CircleCI job parallelism
- [`resource_class: medium`](resource-class.md) — Migrate CircleCI resource classes
- [`- persist_to_workspace / attach_workspace`](workspace.md) — Migrate CircleCI workspaces
- [`jobs: <name>: steps: [...]`](jobs.md) — Migrate CircleCI jobs to GitHub Actions jobs
- [`workflows: <name>: jobs: [{job: {requires, filters, context}}]`](workflows.md) — Migrate CircleCI workflows to GitHub Actions
- [`- <orb-alias>/<command>`](orb-steps.md) — Migrate CircleCI orb command steps
