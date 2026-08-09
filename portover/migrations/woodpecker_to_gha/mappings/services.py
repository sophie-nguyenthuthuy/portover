"""services — sidecar containers (map or list form)."""

from portover.core import MappingMeta

SCOPE = "pipeline"

META = MappingMeta(
    id="services",
    directive="services: (map or list)",
    title="Migrate Woodpecker services to GitHub Actions service containers",
    before="""services:
  database:                 # map form
    image: postgres:16
    environment:
      - POSTGRES_PASSWORD=secret

services:                   # list form, 2.x onwards
  - name: database
    image: postgres:16""",
    after="""services:
  database:
    image: postgres:16
    env:
      POSTGRES_PASSWORD: secret
    options: --health-cmd pg_isready --health-interval 10s --health-retries 5""",
    notes=(
        "Both spellings are accepted and normalise to the same thing. The "
        "hostname rule matches too — the service is reachable at its name — so "
        "connection strings usually need no change. What GHA adds is "
        "readiness: it waits only for the container to start, so a database "
        "that takes a moment to accept connections needs a healthcheck, and "
        "portover attaches one for the images it recognises. Woodpecker's "
        "`environment:` list form becomes the container's `env:` map."
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
    from portover.migrations.woodpecker_to_gha import as_env, as_list

    entries = []
    if isinstance(value, dict):
        entries = [{"name": str(n), **(s if isinstance(s, dict) else {"image": s})}
                   for n, s in value.items()]
    else:
        entries = [s for s in as_list(value) if isinstance(s, dict)]

    for entry in entries:
        name = str(entry.get("name") or "service")
        image = str(entry.get("image") or name)
        spec: dict = {"image": image}
        environment = as_env(entry.get("environment"), ctx)
        if environment:
            spec["env"] = {k: _secret(v) for k, v in environment.items()}
        base = image.split("/")[-1].split(":")[0]
        if base in _HEALTH:
            spec["options"] = _HEALTH[base]
        job.setdefault("services", {})[name] = spec
        if entry.get("commands") or entry.get("command"):
            report.manual(META.id, f"services.{name} command",
                          "GHA service containers cannot override the command — use `options:` "
                          "for docker flags, or start it with `docker run` in a step")
        report.mapped(META.id, f"services: {name}", f"service container {image} (host '{name}')")


def _secret(value):
    if isinstance(value, dict) and "from_secret" in value:
        return "${{ secrets.%s }}" % str(value["from_secret"]).upper()
    return value
