"""services — sidecar containers (declared under definitions)."""

from portover.core import MappingMeta

SCOPE = "step"

META = MappingMeta(
    id="services",
    directive="services: [postgres, redis]",
    title="Migrate Bitbucket Pipelines services to GitHub Actions service containers",
    before="""definitions:
  services:
    postgres:
      image: postgres:16
      variables:
        POSTGRES_PASSWORD: secret

# in a step:
services:
  - postgres""",
    after="""services:
  postgres:
    image: postgres:16
    env:
      POSTGRES_PASSWORD: secret""",
    notes=(
        "Bitbucket splits the definition (under `definitions.services`) from "
        "the use (a step's `services:` list); GHA declares the container inline "
        "on the job, so portover resolves the reference. Note the hostname "
        "rule: Bitbucket services listen on localhost from the step's point of "
        "view, while a GHA service is reachable at its key in the services map "
        "— for a container job, `postgres:5432` rather than `localhost:5432`. "
        "Bitbucket's `variables:` become the container's `env:`, and `memory:` "
        "has no equivalent (GHA does not cap service memory)."
    ),
    priority=22,
)


def matches(key) -> bool:
    return key == "services"


def apply(key, value, job, ctx, report) -> None:
    from portover.migrations.bitbucket_to_gha import as_list

    for name in as_list(value):
        alias = str(name)
        definition = ctx.services.get(alias)
        if definition is None:
            if alias == "docker":
                report.mapped(META.id, "services: docker", "dropped — the docker daemon is available on GHA runners")
                continue
            report.manual(META.id, f"services: {alias}",
                          "no matching definitions.services entry — add the image and ports by hand")
            continue
        spec: dict = {"image": str(definition.get("image", alias))}
        variables = definition.get("variables")
        if isinstance(variables, dict):
            spec["env"] = dict(variables)
        if definition.get("memory"):
            report.mapped(META.id, f"services.{alias}.memory", "dropped — GHA does not cap service memory")
        job.setdefault("services", {})[alias] = spec
        report.mapped(META.id, f"services: {alias}", f"service container {spec['image']} (host '{alias}')")
