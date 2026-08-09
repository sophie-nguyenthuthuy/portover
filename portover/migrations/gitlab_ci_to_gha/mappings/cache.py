"""cache — dependency caching."""

from portover.core import MappingMeta

SCOPE = "job"

META = MappingMeta(
    id="cache",
    directive="cache: key / paths / policy",
    title="Migrate GitLab CI cache to GitHub Actions",
    before="""cache:
  key:
    files:
      - requirements.txt
  paths:
    - .cache/pip""",
    after="""- uses: actions/cache@v4
  with:
    path: .cache/pip
    key: ${{ runner.os }}-${{ hashFiles('requirements.txt') }}""",
    notes=(
        "`key: files:` is the same idea as `hashFiles()` and translates "
        "directly. A plain string key translates too, but watch out: GitLab "
        "*overwrites* a cache under an unchanged key, while GHA caches are "
        "immutable — once written, a key never changes. So a static key like "
        "`key: build-cache` silently stops updating on GHA. Always fold a "
        "content hash into the key. `policy: pull` maps to actions/cache/restore "
        "and `policy: push` to actions/cache/save."
    ),
    priority=28,
)


def matches(key) -> bool:
    return key == "cache"


def apply(key, value, job, ctx, report) -> None:
    from portover.migrations.gitlab_ci_to_gha import as_list

    for entry in as_list(value):
        if isinstance(entry, dict):
            _one(entry, job, ctx, report)
        else:
            report.manual(META.id, f"cache: {entry}", "expected a mapping with paths:")


def _one(spec: dict, job, ctx, report) -> None:
    from portover.migrations.gitlab_ci_to_gha import as_list

    paths = [str(p) for p in as_list(spec.get("paths"))]
    if not paths:
        return
    policy = str(spec.get("policy", "pull-push"))
    action = {"pull": "actions/cache/restore@v4", "push": "actions/cache/save@v4"}.get(policy, "actions/cache@v4")

    key_spec = spec.get("key")
    if isinstance(key_spec, dict) and key_spec.get("files"):
        files = ", ".join(f"'{f}'" for f in as_list(key_spec["files"]))
        key = "${{ runner.os }}-" + "${{ hashFiles(%s) }}" % files
        report.mapped(META.id, f"cache.key.files: {as_list(key_spec['files'])}", "hashFiles() key")
    elif key_spec is not None:
        key = "${{ runner.os }}-" + str(key_spec)
        report.manual(META.id, f"cache.key: {key_spec}",
                      "static key — GHA caches are immutable, so this cache would never update; "
                      "add a ${{ hashFiles('<lockfile>') }} suffix")
    else:
        key = "${{ runner.os }}-cache-${{ github.sha }}"
        report.manual(META.id, "cache without key",
                      "no key given — replace the generated key with a hashFiles() of your lockfile")

    step = {"uses": action, "with": {"path": "\n".join(paths) if len(paths) > 1 else paths[0], "key": key}}
    if action != "actions/cache/save@v4":
        step["with"]["restore-keys"] = "${{ runner.os }}-"
    job.setdefault("_pre_steps", []).append(step)
    report.mapped(META.id, f"cache.paths: {paths}", action)
