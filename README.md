# portover

**Migrate one config dialect to another, one directive at a time.**

You're mid-migration at 2am, searching *"jenkins post always github actions equivalent"*.
portover is the tool — and the doc site — built for exactly that moment.

```console
$ portover detect .
  pip-to-uv: requirements.txt
  jenkins-to-gha: Jenkinsfile

$ portover run jenkins-to-gha .
== jenkins-to-gha: Jenkinsfile (declarative pipeline) -> .github/workflows/*.yml

  + agent        1x
  + stages       4x
  + parallel     1x
  ! triggers     1x

Manual steps:
  ! [environment] API_TOKEN = credentials('api-token')
      create repo secret API_TOKEN with the value of Jenkins credential 'api-token'
  ...

--- .github/workflows/ci.yml (dry run; pass --write to save) ---
```

Dry run by default. `--write` saves the output. Nothing is ever silently dropped:
every source directive is either **mapped**, flagged as a **manual step** with
instructions, or listed as **unmapped** so you know exactly what's left.

## Migrations

| id | from | to |
|---|---|---|
| `pip-to-uv` | requirements.txt (pip) | pyproject.toml (uv) |
| `jenkins-to-gha` | Jenkinsfile (declarative) | .github/workflows/*.yml |
| `travis-to-gha` | .travis.yml (Travis CI) | .github/workflows/*.yml |
| `gitlab-ci-to-gha` | .gitlab-ci.yml (GitLab CI) | .github/workflows/*.yml |
| `circleci-to-gha` | .circleci/config.yml (CircleCI) | .github/workflows/*.yml |
| `azure-pipelines-to-gha` | azure-pipelines.yml (Azure Pipelines) | .github/workflows/*.yml |
| `bitbucket-to-gha` | bitbucket-pipelines.yml (Bitbucket) | .github/workflows/*.yml |
| `buildkite-to-gha` | Buildkite pipeline.yml | .github/workflows/*.yml |
| `drone-to-gha` | .drone.yml (Drone CI) | .github/workflows/*.yml |
| `flake8-to-ruff` | .flake8 / setup.cfg | ruff.toml |

Browse [docs/](docs/index.md) — one page per directive, generated from the
mappings themselves, so the docs can never drift from the code.

## Install

```console
pip install portover   # or: uv tool install portover
```

Zero dependencies, stdlib only, Python ≥ 3.11.

## The design in one paragraph

A **migration** is a folder. A **mapping** is one small file in it that handles
exactly one source directive — `-e`, `post { failure }`, `max-line-length` —
with a `matches()`, an `apply()`, and a `META` block holding a real
before/after example. Mappings register themselves by existing (the folder is
scanned), the docs are generated from `META`, and the report the CLI prints is
the same data. Fix the mapping and the converter, the docs page, and the
report all update together.

## Contributing

The contributor unit is **one mapping for one directive** — a ~40-line file
plus a test. If portover printed `? unmapped` for something in your migration,
that's the file you get to write. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT
