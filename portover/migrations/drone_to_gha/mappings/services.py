"""services — sidecar containers."""

from portover.core import MappingMeta

SCOPE = "pipeline"

META = MappingMeta(
    id="services",
    directive="services: [{name, image, environment}]",
    title="Migrate Drone services to GitHub Actions service containers",
    before="""services:
  - name: database
    image: postgres:16
    environment:
      POSTGRES_PASSWORD: secret""",
    after="""services:
  database:
    image: postgres:16
    env:
      POSTGRES_PASSWORD: secret""",
    notes=(
        "Close to a rename — both run sidecars on a shared network for the "
        "duration, and in both the service is reachable at its NAME as "
        "hostname, so connection strings usually need no change. Drone's "
        "`environment:` becomes `env:`, including `from_secret` references, "
        "which are rewritten to `${{ secrets.* }}`. Where they differ: GHA "
        "waits only for the container to start unless you give it "
        "`options: --health-cmd`, so a service that needs a moment to become "
        "ready (Postgres, MySQL) should get a healthcheck — portover adds one "
        "for the databases it recognises."
    ),
    priority=16,
)

_HEALTH = {
    "postgres": "--health-cmd pg_isready --health-interval 10s --health-timeout 5s --health-retries 5",
    "mysql": '--health-cmd "mysqladmin ping" --health-interval 10s --health-timeout 5s --health-retries 5',
    "mariadb": '--health-cmd "mysqladmin ping" --health-interval 10s --health-timeout 5s --health-retries 5',
    "redis": '--health-cmd "redis-cli ping" --health-interval 10s --health-timeout 5s --health-retries 5',
}


def matches(key) -> bool:
    return key == "services"


def apply(key, value, job, ctx, report) -> None:
    from portover.migrations.drone_to_gha import as_list, secret_ref

    for entry in as_list(value):
        if not isinstance(entry, dict):
            continue
        name = str(entry.get("name") or "service")
        image = str(entry.get("image") or name)
        spec: dict = {"image": image}
        environment = entry.get("environment")
        if isinstance(environment, dict):
            spec["env"] = {str(k): secret_ref(v, ctx, report) for k, v in environment.items()}
        base = image.split("/")[-1].split(":")[0]
        if base in _HEALTH:
            spec["options"] = _HEALTH[base]
        job.setdefault("services", {})[name] = spec
        if entry.get("commands") or entry.get("command"):
            report.manual(META.id, f"services.{name} command",
                          "GHA service containers cannot override the command — use "
                          "`options:` for docker flags, or start it with `docker run` in a step")
        report.mapped(META.id, f"services: {name}", f"service container {image} (host '{name}')")
