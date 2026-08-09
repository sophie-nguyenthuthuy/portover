"""services — sidecar containers."""

from portover.core import MappingMeta

SCOPE = "job"

META = MappingMeta(
    id="services",
    directive="services: [postgres:16, {name, alias}]",
    title="Migrate GitLab CI services to GitHub Actions service containers",
    before="""services:
  - postgres:16
  - name: redis:7
    alias: cache""",
    after="""services:
  postgres:
    image: postgres:16
    env: { POSTGRES_PASSWORD: postgres }
  cache:
    image: redis:7""",
    notes=(
        "Both systems run sidecars on a shared network, but the hostname rule "
        "differs and this is where migrations break: in GitLab a service is "
        "reachable at its image name or `alias`, in GHA at its *key* in the "
        "services map. portover uses the alias when there is one and the image's "
        "base name otherwise. Also note GHA does not read GitLab's "
        "`POSTGRES_PASSWORD`-style variables from the job automatically — the "
        "service needs its own `env:`, and portover seeds the well-known ones."
    ),
    priority=14,
)

_SEED_ENV = {
    "postgres": {"POSTGRES_PASSWORD": "postgres"},
    "mysql": {"MYSQL_ALLOW_EMPTY_PASSWORD": "yes"},
    "mariadb": {"MYSQL_ALLOW_EMPTY_PASSWORD": "yes"},
    "mongo": {},
    "redis": {},
}


def matches(key) -> bool:
    return key == "services"


def apply(key, value, job, ctx, report) -> None:
    from portover.migrations.gitlab_ci_to_gha import as_list

    for entry in as_list(value):
        if isinstance(entry, dict):
            image = str(entry.get("name", ""))
            alias = str(entry.get("alias") or "") or _base(image)
            if entry.get("command") or entry.get("entrypoint"):
                report.manual(META.id, f"services.{alias} command/entrypoint",
                              "GHA service containers take `options:` for docker flags — move it there")
        else:
            image = str(entry)
            alias = _base(image)
        if not image:
            continue
        spec: dict = {"image": image}
        seed = _SEED_ENV.get(_base(image))
        if seed:
            spec["env"] = dict(seed)
        job.setdefault("services", {})[alias] = spec
        report.mapped(META.id, f"services: {image}", f"service '{alias}' (reachable at that hostname)")


def _base(image: str) -> str:
    return image.split("/")[-1].split(":")[0] or "service"
