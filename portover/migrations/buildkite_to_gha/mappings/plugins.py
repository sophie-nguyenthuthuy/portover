"""plugins — Buildkite's reusable step units."""

from portover.core import MappingMeta

SCOPE = "step"

META = MappingMeta(
    id="plugins",
    directive="plugins: [org/name#v1.0.0: {config}]",
    title="Migrate Buildkite plugins to GitHub Actions",
    before="""plugins:
  - docker#v5.10.0:
      image: python:3.12
  - artifacts#v1.9.0:
      upload: dist/**
  - ecr#v2.7.0:
      login: true""",
    after="""container: python:3.12          # docker plugin
steps:
  - uses: aws-actions/amazon-ecr-login@v2   # ecr plugin
  - uses: actions/upload-artifact@v4        # artifacts plugin
    with: {name: build, path: dist/**}""",
    notes=(
        "Plugins are Buildkite's answer to actions, so the common ones have "
        "real counterparts and portover translates those: docker becomes the "
        "job's `container:`, artifacts becomes upload-/download-artifact, cache "
        "becomes actions/cache, ecr becomes amazon-ecr-login. The mismatch to "
        "watch is lifecycle — a Buildkite plugin can hook before AND after the "
        "command (docker-login logs in first, junit-annotate reports "
        "afterwards), while a GHA action is just a step in a sequence, so the "
        "ordering becomes explicit. Plugins with no equivalent become a visible "
        "TODO step rather than vanishing."
    ),
    priority=18,
)

_HINTS = {
    "docker-compose": "run `docker compose` from a run step (the daemon is available on GHA runners)",
    "docker-login": "use docker/login-action@v3 with a registry secret",
    "junit-annotate": "GHA has no test-report UI — upload the XML and add dorny/test-reporter",
    "test-collector": "upload results as an artifact, or use your vendor's own action",
    "shellcheck": "use a shellcheck action, or run shellcheck directly in a run step",
    "golang": "use actions/setup-go@v5",
    "nodejs": "use actions/setup-node@v4",
    "python": "use actions/setup-python@v5",
    "monorepo-diff": "use dorny/paths-filter and gate jobs on its outputs",
    "github-merged-pr": "read the PR from the github context (github.event.pull_request)",
    "s3-cache": "use actions/cache@v4, or an S3-backed cache action",
    "block-step": "use an Environment with required reviewers",
}


def matches(key) -> bool:
    return key == "plugins"


def apply(key, value, job, ctx, report) -> None:
    from portover.migrations.buildkite_to_gha import as_list

    for entry in as_list(value):
        if isinstance(entry, str):
            name, config = entry, {}
        elif isinstance(entry, dict) and len(entry) == 1:
            (name, config), = entry.items()
            config = config if isinstance(config, dict) else {}
        else:
            report.unmapped.append(f"plugin: {entry!r}")
            continue
        base = str(name).split("#")[0].split("/")[-1]
        if not _translate(base, config, job, ctx, report, raw=str(name)):
            hint = _HINTS.get(base, "no direct equivalent — search the GitHub Marketplace for this plugin")
            report.manual(META.id, f"plugin: {name}", hint)
            job.setdefault("_pre_steps", []).append(
                {"run": f"echo 'TODO: port Buildkite plugin {name} — {hint}'"})


def _translate(base, config, job, ctx, report, *, raw) -> bool:
    from portover.migrations.buildkite_to_gha import as_list

    if base == "docker":
        image = config.get("image")
        if not image:
            return False
        container: dict = {"image": str(image)}
        if config.get("user"):
            container["options"] = f"--user {config['user']}"
        env = config.get("environment")
        if isinstance(env, list):
            report.manual(META.id, f"plugin {raw}: environment passthrough",
                          "the docker plugin forwards named variables into the container — "
                          "GHA container jobs already inherit the job env")
        job["container"] = container if len(container) > 1 else container["image"]
        report.mapped(META.id, f"plugin: {raw}", f"container: {image}")
        return True

    if base == "artifacts":
        upload = config.get("upload")
        download = config.get("download")
        if upload is not None:
            paths = [str(p) for p in as_list(upload)]
            job.setdefault("_post_steps", []).append(
                {"uses": "actions/upload-artifact@v4",
                 "with": {"name": ctx.current_jid or "artifacts",
                          "path": "\n".join(paths) if len(paths) > 1 else paths[0]}})
            job.setdefault("_artifacts", []).append(ctx.current_jid or "artifacts")
            report.mapped(META.id, f"plugin: {raw} (upload)", "actions/upload-artifact@v4")
        if download is not None:
            job.setdefault("_pre_steps", []).append({"uses": "actions/download-artifact@v4"})
            report.manual(META.id, f"plugin: {raw} (download)",
                          "added download-artifact — set `name:` to the artifact the producing job uploaded")
        return upload is not None or download is not None

    if base == "cache":
        paths = [str(p) for p in as_list(config.get("path") or config.get("paths"))]
        if not paths:
            return False
        key_expr = str(config.get("key") or "${{ runner.os }}-cache-${{ github.sha }}")
        if "{{" in key_expr or "checksum" in key_expr:
            report.manual(META.id, f"plugin: {raw} key",
                          "translate the cache key template into a ${{ hashFiles('<lockfile>') }} expression")
            key_expr = "${{ runner.os }}-cache-${{ hashFiles('**/lockfile') }}"
        job.setdefault("_pre_steps", []).append(
            {"uses": "actions/cache@v4",
             "with": {"path": "\n".join(paths) if len(paths) > 1 else paths[0], "key": key_expr}})
        report.mapped(META.id, f"plugin: {raw}", "actions/cache@v4")
        return True

    if base == "ecr":
        job.setdefault("_pre_steps", []).append({"uses": "aws-actions/amazon-ecr-login@v2"})
        report.manual(META.id, f"plugin: {raw}",
                      "added amazon-ecr-login — it needs aws-actions/configure-aws-credentials "
                      "before it (prefer OIDC over stored keys)")
        return True
    return False
