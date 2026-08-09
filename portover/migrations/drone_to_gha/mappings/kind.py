"""kind / type — what a document in the stream is."""

from portover.core import MappingMeta

SCOPE = "pipeline"

META = MappingMeta(
    id="kind",
    directive="kind: pipeline / secret / signature — and type: docker / exec / ssh",
    title="Migrate Drone document kinds to GitHub Actions",
    before="""kind: pipeline
type: docker
name: default
---
kind: secret
name: docker_password
get:
  path: secret/data/docker
  name: password""",
    after="""# only pipelines produce jobs; the rest have no YAML equivalent:
#   kind: secret    -> a repository or organisation secret
#   kind: signature -> nothing (Drone's config signing)""",
    notes=(
        "A .drone.yml is a stream of documents and only `kind: pipeline` ones "
        "become jobs. `kind: secret` declares where Drone fetches a secret "
        "(often Vault) — recreate it as a GitHub secret, or wire the same "
        "vault with hashicorp/vault-action. `kind: signature` is the HMAC that "
        "signs the config for unverified repositories and has no counterpart. "
        "The pipeline `type:` matters too: `docker` is the normal case, `exec` "
        "runs directly on an agent (closest to a self-hosted runner, and its "
        "steps have no images), and `ssh`/`kubernetes`/`digitalocean` types "
        "describe infrastructure GHA does not model, so those are flagged."
    ),
    priority=10,
)

_TYPES = {"docker", "exec"}


def matches(key) -> bool:
    return key == "type"


def apply(key, value, job, ctx, report) -> None:
    kind = str(value)
    if kind == "exec":
        job["runs-on"] = ["self-hosted"]
        report.manual(META.id, "type: exec",
                      "an exec pipeline runs straight on the agent — the equivalent is a "
                      "self-hosted runner (or GitHub-hosted, if the tools are available there)")
        return
    report.mapped(META.id, f"type: {kind}")


def is_pipeline(document: dict, ctx, report) -> bool:
    """Decide whether a document in the stream becomes a job."""
    kind = str(document.get("kind", "pipeline"))
    name = str(document.get("name", "?"))
    if kind == "pipeline":
        kind_type = str(document.get("type", "docker"))
        if kind_type not in _TYPES:
            report.manual(META.id, f"pipeline {name}: type: {kind_type}",
                          f"`{kind_type}` pipelines describe infrastructure GHA does not model — "
                          "convert the steps by hand onto a hosted or self-hosted runner")
            return False
        return True
    if kind == "secret":
        report.manual(META.id, f"kind: secret ({name})",
                      "declares an external secret source — recreate it as a GitHub secret, "
                      "or fetch it with hashicorp/vault-action")
        return False
    if kind == "signature":
        report.mapped(META.id, "kind: signature", "dropped — GHA does not sign workflow files")
        return False
    if kind == "template":
        report.manual(META.id, f"kind: template ({name})",
                      "a Drone template — the GHA equivalent is a reusable workflow "
                      "(on: workflow_call) or a composite action")
        return False
    report.unmapped.append(f"kind: {kind}")
    return False
