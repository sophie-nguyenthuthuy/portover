"""services — postgresql/mysql/redis/mongodb/rabbitmq/docker."""

from portover.core import MappingMeta

META = MappingMeta(
    id="services",
    directive="services: postgresql / redis / mysql / docker ...",
    title="Migrate Travis services to GitHub Actions service containers",
    before="services:\n  - postgresql\n  - redis",
    after="""services:
  postgres:
    image: postgres:16
    env: { POSTGRES_PASSWORD: postgres }
    ports: ["5432:5432"]
    options: --health-cmd pg_isready --health-interval 10s --health-retries 5
  redis:
    image: redis:7
    ports: ["6379:6379"]""",
    notes=(
        "Travis services listened on localhost with no auth; GHA service "
        "containers need explicit ports and (for postgres/mysql) a password — "
        "update your test config accordingly. `docker` needs no service at "
        "all: the docker daemon is already available on GHA runners."
    ),
    priority=20,
)

_SERVICES = {
    "postgresql": ("postgres", {
        "image": "postgres:16",
        "env": {"POSTGRES_PASSWORD": "postgres"},
        "ports": ["5432:5432"],
        "options": "--health-cmd pg_isready --health-interval 10s --health-timeout 5s --health-retries 5",
    }),
    "mysql": ("mysql", {
        "image": "mysql:8",
        "env": {"MYSQL_ALLOW_EMPTY_PASSWORD": "yes"},
        "ports": ["3306:3306"],
        "options": '--health-cmd "mysqladmin ping" --health-interval 10s --health-timeout 5s --health-retries 5',
    }),
    "redis": ("redis", {"image": "redis:7", "ports": ["6379:6379"]}),
    "mongodb": ("mongo", {"image": "mongo:7", "ports": ["27017:27017"]}),
    "rabbitmq": ("rabbitmq", {"image": "rabbitmq:3", "ports": ["5672:5672"]}),
    "memcached": ("memcached", {"image": "memcached:1", "ports": ["11211:11211"]}),
    "elasticsearch": ("elasticsearch", {
        "image": "elasticsearch:8.15.0",
        "env": {"discovery.type": "single-node", "xpack.security.enabled": "false"},
        "ports": ["9200:9200"],
    }),
}


def matches(key) -> bool:
    return key == "services"


def apply(key, value, ctx, report) -> None:
    for svc in (value if isinstance(value, list) else [value]):
        name = str(svc)
        if name == "docker":
            report.mapped(META.id, "services: docker", "dropped — docker is preinstalled on GHA runners")
            continue
        if name in _SERVICES:
            gha_name, spec = _SERVICES[name]
            ctx.services[gha_name] = dict(spec)
            report.mapped(META.id, f"services: {name}", f"service container {spec['image']}")
        else:
            report.manual(META.id, f"services: {name}",
                          "add a service container with the right image/ports (see the services doc page)")
