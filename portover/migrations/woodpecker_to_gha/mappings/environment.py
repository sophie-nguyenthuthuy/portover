"""environment / secrets — step variables and secret references."""

from portover.core import MappingMeta

SCOPE = "step"

META = MappingMeta(
    id="environment",
    directive="environment: (map or KEY=value list) / secrets: / from_secret",
    title="Migrate Woodpecker environment and secrets to GitHub Actions",
    before="""environment:
  - GOOS=linux              # list form
  TOKEN:
    from_secret: api_token  # map form
secrets: [docker_password]  # pre-2.0 spelling""",
    after="""env:
  GOOS: linux
  TOKEN: ${{ secrets.API_TOKEN }}
  DOCKER_PASSWORD: ${{ secrets.DOCKER_PASSWORD }}""",
    notes=(
        "`environment:` accepts a map or a list of `KEY=value` strings, and "
        "portover normalises both. Secrets have two spellings across "
        "Woodpecker versions: the modern `from_secret:` on a variable, and the "
        "older top-level `secrets: [name]` list, which injected each secret as "
        "an upper-cased environment variable of the same name — both become "
        "`${{ secrets.NAME }}`. Nothing sensitive is carried over either way, "
        "because the values live in Woodpecker's settings, not in this file; "
        "recreate them under Settings > Secrets and variables."
    ),
    priority=14,
)


def matches(key) -> bool:
    return key in ("environment", "secrets")


def apply(key, value, step, ctx, report) -> None:
    from portover.migrations.woodpecker_to_gha import as_env, as_list, note_vars

    env = step.setdefault("env", {})
    if key == "secrets":
        for entry in as_list(value):
            if isinstance(entry, dict):  # {source: x, target: Y}
                source = str(entry.get("source") or entry.get("name") or "")
                target = str(entry.get("target") or source).upper()
            else:
                source = str(entry)
                target = source.upper()
            if not source:
                continue
            env[target] = "${{ secrets.%s }}" % target
            report.manual(META.id, f"secrets: {source}",
                          f"create repository secret {target} — Woodpecker secrets are not in the file")
        ctx.step_env = env
        return

    for name, spec in as_env(value, ctx).items():
        if isinstance(spec, dict) and "from_secret" in spec:
            secret = str(spec["from_secret"]).upper()
            env[name] = "${{ secrets.%s }}" % secret
            report.manual(META.id, f"{name}: from_secret {spec['from_secret']}",
                          f"create repository secret {secret} — Woodpecker secrets are not in the file")
        else:
            note_vars(spec, ctx)
            env[name] = spec
            report.mapped(META.id, f"environment.{name}")
    if not env:
        step.pop("env", None)
    ctx.step_env = env
