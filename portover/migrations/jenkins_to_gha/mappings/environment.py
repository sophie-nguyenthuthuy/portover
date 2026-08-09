"""environment — env vars and credentials()."""

import re

from portover.core import MappingMeta

SCOPE = "pipeline"

META = MappingMeta(
    id="environment",
    directive="environment { KEY = 'value' }",
    title="Migrate Jenkins environment blocks to GitHub Actions env",
    before="""environment {
  REGISTRY = 'ghcr.io'
  API_TOKEN = credentials('api-token')
}""",
    after="""env:
  REGISTRY: ghcr.io
  API_TOKEN: ${{ secrets.API_TOKEN }}""",
    notes=(
        "Plain assignments map 1:1. `credentials('id')` becomes a repository "
        "secret — create it under Settings > Secrets and variables > Actions. "
        "Jenkins usernamePassword credentials split into TWO secrets (_USR/_PSW)."
    ),
    priority=12,
)

_CRED = re.compile(r"credentials\(\s*['\"]([^'\"]+)['\"]\s*\)")


def matches(node) -> bool:
    return node.keyword() == "environment"


def parse_env(node, report) -> dict:
    """Shared with stages.py for stage-level environment blocks."""
    env: dict = {}
    for stmt in node.stmts:
        if "=" not in stmt:
            continue
        key, _, val = stmt.partition("=")
        key, val = key.strip(), val.strip()
        cred = _CRED.search(val)
        if cred:
            secret = re.sub(r"[^A-Za-z0-9_]", "_", cred.group(1)).upper()
            env[key] = "${{ secrets.%s }}" % secret
            report.manual(META.id, stmt, f"create repo secret {secret} with the value of Jenkins credential '{cred.group(1)}'")
        else:
            env[key] = val.strip("'\"")
            report.mapped(META.id, stmt)
    return env


def apply(node, ctx, report) -> None:
    ctx.env.update(parse_env(node, report))
