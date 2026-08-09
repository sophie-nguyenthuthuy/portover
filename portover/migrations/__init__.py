"""Migration registry. Adding a migration = import its MIGRATION here."""

from portover.migrations.flake8_to_ruff import MIGRATION as flake8_to_ruff
from portover.migrations.gitlab_ci_to_gha import MIGRATION as gitlab_ci_to_gha
from portover.migrations.azure_pipelines_to_gha import MIGRATION as azure_pipelines_to_gha
from portover.migrations.circleci_to_gha import MIGRATION as circleci_to_gha
from portover.migrations.jenkins_to_gha import MIGRATION as jenkins_to_gha
from portover.migrations.pip_to_uv import MIGRATION as pip_to_uv
from portover.migrations.travis_to_gha import MIGRATION as travis_to_gha

REGISTRY = [pip_to_uv, jenkins_to_gha, travis_to_gha, circleci_to_gha, gitlab_ci_to_gha, azure_pipelines_to_gha, flake8_to_ruff]


def get(migration_id: str):
    for m in REGISTRY:
        if m.id == migration_id:
            return m
    raise KeyError(migration_id)
