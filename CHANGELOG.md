# Changelog

## 0.3.0 — 2026-08-09

### Added

- Added `circleci-to-gha`, converting `.circleci/config.yml` and
  `.circleci/config.yaml` into GitHub Actions workflows.
- Added 24 directive mappings covering workflows, job dependencies, filters,
  matrices, approval gates, executors, containers, services, reusable commands,
  parameters, caches, artifacts, workspaces, shells, and parallelism.
- Added a kitchen-sink CircleCI example and generated documentation for every
  new mapping.
- Added explicit manual-review guidance for non-portable concepts including
  orbs, contexts, resource classes, service networking, and test splitting.

### Changed

- Promoted the stdlib-only mini YAML reader to `portover.miniyaml` so YAML-based
  migrations can share it.
- Extended the YAML reader with block scalars and nested flow collections used
  by real CircleCI configurations.

### Validation

- Tested on Python 3.11, 3.12, and 3.13.
- Verified generated documentation and built wheel/source distributions.

## 0.2.0 — 2026-08-09

- Added the `travis-to-gha` migration with 12 directive mappings.
- Added the original stdlib-only mini YAML reader.

## 0.1.0 — 2026-08-09

- Initial release with pip-to-uv, Jenkins-to-GitHub-Actions, and
  flake8-to-ruff migrations.
- Added tag-driven PyPI trusted publishing.
