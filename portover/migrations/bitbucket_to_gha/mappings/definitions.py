"""definitions — reusable caches, services and step anchors."""

from portover.core import MappingMeta

SCOPE = "pipeline"

META = MappingMeta(
    id="definitions",
    directive="definitions: caches / services / steps",
    title="Migrate Bitbucket Pipelines definitions to GitHub Actions",
    before="""definitions:
  caches:
    sonar: ~/.sonar/cache
  services:
    postgres:
      image: postgres:16
      variables:
        POSTGRES_PASSWORD: secret""",
    after="""# no definitions block — each is inlined where it is used:
#   caches   -> actions/cache path in the job that listed it
#   services -> the job's services: map""",
    notes=(
        "`definitions:` is a declaration area, not something that runs, so it "
        "produces no output of its own — portover records the entries and "
        "resolves them wherever a step references them. `definitions.steps` "
        "holds YAML-anchored step templates (`&build-step`), and anchors are "
        "the one construct portover's reader refuses rather than guesses at: if "
        "your config uses them, expand them first. The GHA equivalent of a "
        "shared step template is a composite action or a reusable workflow."
    ),
    priority=18,
)


def matches(key) -> bool:
    return key == "definitions"


def apply(key, value, ctx, report) -> None:
    if not isinstance(value, dict):
        return
    caches = value.get("caches")
    if isinstance(caches, dict):
        for name, path in caches.items():
            ctx.caches[str(name)] = path
            report.mapped(META.id, f"definitions.caches.{name}", "resolved where a step lists it")
    services = value.get("services")
    if isinstance(services, dict):
        for name, spec in services.items():
            ctx.services[str(name)] = spec if isinstance(spec, dict) else {"image": spec}
            report.mapped(META.id, f"definitions.services.{name}", "resolved where a step lists it")
    if value.get("steps"):
        report.manual(META.id, "definitions.steps",
                      "shared step templates — extract them into a composite action "
                      "(.github/actions/<name>/action.yml) or a reusable workflow")
    for extra in set(value) - {"caches", "services", "steps", "pipelines"}:
        report.unmapped.append(f"definitions.{extra}")
