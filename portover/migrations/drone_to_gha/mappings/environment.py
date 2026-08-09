"""environment — step variables and Drone secrets."""

from portover.core import MappingMeta

SCOPE = "step"

META = MappingMeta(
    id="environment",
    directive="environment: {NAME: value, NAME: {from_secret: x}}",
    title="Migrate Drone environment and from_secret to GitHub Actions",
    before="""environment:
  GOOS: linux
  DOCKER_PASSWORD:
    from_secret: docker_password""",
    after="""env:
  GOOS: linux
  DOCKER_PASSWORD: ${{ secrets.DOCKER_PASSWORD }}""",
    notes=(
        "Plain values map straight to the step's `env:`. `from_secret:` is the "
        "interesting one — it names a secret stored in Drone (repository, "
        "organisation, or a `kind: secret` document), never a value in the "
        "file, so nothing sensitive is carried over. portover rewrites the "
        "reference to `${{ secrets.NAME }}`, upper-casing the Drone name "
        "because GitHub secret names are case-insensitive and conventionally "
        "upper-case; create each one under Settings > Secrets and variables."
    ),
    priority=14,
)


def matches(key) -> bool:
    return key == "environment"


def apply(key, value, step, ctx, report) -> None:
    from portover.migrations.drone_to_gha import note_vars, secret_ref

    if not isinstance(value, dict):
        return
    env = {}
    for name, spec in value.items():
        if isinstance(spec, dict) and "from_secret" in spec:
            env[str(name)] = secret_ref(spec, ctx, report)
            report.manual(META.id, f"{name}: from_secret {spec['from_secret']}",
                          f"create repository secret {env[str(name)].strip('${ }').replace('secrets.', '')} "
                          "— Drone secrets are not stored in the file")
        else:
            note_vars(spec, ctx)
            env[str(name)] = spec
            report.mapped(META.id, f"environment.{name}")
    if env:
        step["env"] = env
        ctx.step_env = env  # forwarded with -e when the step runs via docker run
