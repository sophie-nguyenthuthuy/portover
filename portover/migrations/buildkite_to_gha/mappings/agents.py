"""agents — which agent runs the step."""

from portover.core import MappingMeta

SCOPE = "step"

META = MappingMeta(
    id="agents",
    directive="agents: {queue: default, os: linux}",
    title="Migrate Buildkite agents to GitHub Actions runs-on",
    before="""agents:
  queue: builders
  os: linux""",
    after="runs-on: [self-hosted, builders, linux]",
    notes=(
        "Buildkite is agent-based: you run the machines, and `agents:` is a "
        "tag query that picks one. The faithful translation is a self-hosted "
        "runner carrying the same labels, which is what portover emits — but "
        "it is worth asking whether the step needs a specific machine at all, "
        "because GitHub-hosted runners (`runs-on: ubuntu-latest`) remove the "
        "fleet you were maintaining. A queue named for an OS or size usually "
        "translates to a hosted runner instead; a queue named for private "
        "network access or special hardware genuinely needs self-hosted."
    ),
    priority=22,
)

_HOSTED = {"linux": "ubuntu-latest", "ubuntu": "ubuntu-latest",
           "macos": "macos-latest", "darwin": "macos-latest", "windows": "windows-latest"}


def matches(key) -> bool:
    return key == "agents"


def apply(key, value, job, ctx, report) -> None:
    from portover.migrations.buildkite_to_gha import as_list

    tags = {}
    if isinstance(value, dict):
        tags = {str(k): str(v) for k, v in value.items()}
    else:  # list form: ["queue=builders", "os=linux"]
        for entry in as_list(value):
            text = str(entry)
            if "=" in text:
                k, _, v = text.partition("=")
                tags[k.strip()] = v.strip()
    if not tags:
        return

    labels = [v for v in tags.values() if v]
    if len(tags) == 1 and next(iter(tags.values())).lower() in _HOSTED:
        job["runs-on"] = _HOSTED[next(iter(tags.values())).lower()]
        report.mapped(META.id, f"agents: {tags}", f"runs-on: {job['runs-on']}")
        return
    job["runs-on"] = ["self-hosted", *labels]
    report.manual(META.id, f"agents: {tags}",
                  f"mapped to {job['runs-on']} — register those agents as GitHub self-hosted "
                  "runners with matching labels, or switch to a GitHub-hosted runner if the "
                  "queue was only selecting an OS or size")


def apply_pipeline(value, ctx, report) -> None:
    ctx.default_agents = value
    report.mapped(META.id, "agents (pipeline)", "applied to every step that has no agents of its own")
