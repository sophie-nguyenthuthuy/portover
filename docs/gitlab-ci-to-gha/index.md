# gitlab-ci-to-gha: .gitlab-ci.yml (GitLab CI) → .github/workflows/*.yml (GitHub Actions)

Run it: `portover run gitlab-ci-to-gha <dir>` (dry run) then `--write`.

One page per directive:

- [`extends: .template`](extends.md) — Migrate GitLab CI extends to GitHub Actions
- [`script / before_script / after_script`](script.md) — Migrate GitLab CI script blocks to GitHub Actions run steps
- [`stages: [build, test, deploy]`](stages.md) — Migrate GitLab CI stages to GitHub Actions needs
- [`image: name / image: {name, entrypoint}`](image.md) — Migrate GitLab CI image to GitHub Actions container
- [`variables: (global)`](variables.md) — Migrate GitLab CI global variables to GitHub Actions env
- [`default: / top-level image, services, before_script, after_script, cache`](defaults.md) — Migrate the GitLab CI default block to GitHub Actions
- [`services: [postgres:16, {name, alias}]`](services.md) — Migrate GitLab CI services to GitHub Actions service containers
- [`include: local / project / remote / template`](include.md) — Migrate GitLab CI include to GitHub Actions
- [`<job>.variables`](job-variables.md) — Migrate GitLab CI job variables to GitHub Actions
- [`workflow: rules / name`](workflow-rules.md) — Migrate GitLab CI workflow rules to GitHub Actions triggers
- [`rules: [{if, changes, exists, when, allow_failure}]`](rules.md) — Migrate GitLab CI rules to GitHub Actions if conditions
- [`only: / except:`](only-except.md) — Migrate GitLab CI only and except to GitHub Actions
- [`needs: [job] / needs: [{job, artifacts, optional}]`](needs.md) — Migrate GitLab CI needs to GitHub Actions
- [`artifacts: paths / reports / expire_in / when`](artifacts.md) — Migrate GitLab CI artifacts to GitHub Actions
- [`cache: key / paths / policy`](cache.md) — Migrate GitLab CI cache to GitHub Actions
- [`parallel: N / parallel: matrix:`](parallel.md) — Migrate GitLab CI parallel to GitHub Actions matrix
- [`tags: [docker, linux]`](tags.md) — Migrate GitLab CI runner tags to GitHub Actions runs-on
- [`when: manual / always / on_failure / delayed`](when.md) — Migrate GitLab CI when to GitHub Actions
- [`allow_failure: true / {exit_codes}`](allow-failure.md) — Migrate GitLab CI allow_failure to GitHub Actions
- [`timeout: 1h 30m`](timeout.md) — Migrate GitLab CI timeout to GitHub Actions
- [`retry: 2 / retry: {max, when}`](retry.md) — Migrate GitLab CI retry to GitHub Actions
- [`environment: name / url / on_stop`](environment.md) — Migrate GitLab CI environment to GitHub Actions
- [`dependencies: [build]`](dependencies.md) — Migrate GitLab CI dependencies to GitHub Actions
- [`interruptible: true / resource_group: production`](concurrency.md) — Migrate GitLab CI interruptible and resource_group to GitHub Actions
- [`trigger: project / include / strategy`](trigger.md) — Migrate GitLab CI trigger to GitHub Actions
- [`coverage: /regex/`](coverage.md) — Migrate GitLab CI coverage regex to GitHub Actions
- [`<job name>: (any top-level key that is not a pipeline setting)`](jobs.md) — Migrate GitLab CI jobs to GitHub Actions jobs
- [`$CI_COMMIT_SHA, $CI_COMMIT_BRANCH, $CI_REGISTRY_IMAGE, ...`](ci-variables.md) — Migrate GitLab CI predefined variables to GitHub Actions
