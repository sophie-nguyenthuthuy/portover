"""caches — named dependency caches."""

from portover.core import MappingMeta

SCOPE = "step"

META = MappingMeta(
    id="caches",
    directive="caches: [node, pip, custom-name]",
    title="Migrate Bitbucket Pipelines caches to GitHub Actions",
    before="""caches:
  - node
  - pip""",
    after="""- uses: actions/cache@v4
  with:
    path: node_modules
    key: ${{ runner.os }}-node-${{ hashFiles('**/package-lock.json') }}""",
    notes=(
        "Bitbucket ships named caches that already know their path (node, pip, "
        "maven, gradle...); GHA has no such registry, so portover expands each "
        "name into the path and a lockfile-hashed key. The difference to watch "
        "is invalidation: a Bitbucket cache is keyed by name and silently "
        "refreshed roughly weekly, while a GHA cache key is immutable — which "
        "is why the generated keys hash a lockfile. Check that the hashed file "
        "is the right one for your project. The `docker` cache has no "
        "equivalent; use docker/build-push-action's gha cache backend instead."
    ),
    priority=18,
)

# Bitbucket named cache -> (path, lockfile glob for the key)
_NAMED = {
    "node": ("node_modules", "**/package-lock.json"),
    "npm": ("~/.npm", "**/package-lock.json"),
    "yarn": ("~/.cache/yarn", "**/yarn.lock"),
    "pip": ("~/.cache/pip", "**/requirements*.txt"),
    "pipenv": ("~/.local/share/virtualenvs", "**/Pipfile.lock"),
    "poetry": ("~/.cache/pypoetry", "**/poetry.lock"),
    "maven": ("~/.m2/repository", "**/pom.xml"),
    "gradle": ("~/.gradle/caches", "**/*.gradle*"),
    "sbt": ("~/.ivy2/cache", "**/build.sbt"),
    "composer": ("~/.composer/cache", "**/composer.lock"),
    "bundler": ("vendor/bundle", "**/Gemfile.lock"),
    "dotnetcore": ("~/.nuget/packages", "**/*.csproj"),
    "nuget": ("~/.nuget/packages", "**/packages.lock.json"),
    "go": ("~/go/pkg/mod", "**/go.sum"),
    "cargo": ("~/.cargo/registry", "**/Cargo.lock"),
}


def matches(key) -> bool:
    return key == "caches"


def apply(key, value, job, ctx, report) -> None:
    from portover.migrations.bitbucket_to_gha import as_list

    for name in as_list(value):
        cache = str(name)
        if cache == "docker":
            report.manual(META.id, "caches: docker",
                          "no docker layer cache action — use docker/build-push-action with "
                          "cache-from/cache-to: type=gha")
            continue
        if cache in _NAMED:
            path, lockfile = _NAMED[cache]
            key_expr = "${{ runner.os }}-%s-${{ hashFiles('%s') }}" % (cache, lockfile)
            report.mapped(META.id, f"caches: {cache}", f"actions/cache path {path}")
        elif cache in ctx.caches:
            path = str(ctx.caches[cache])
            key_expr = "${{ runner.os }}-%s-${{ github.sha }}" % cache
            report.manual(META.id, f"caches: {cache} (custom)",
                          "custom cache key is content-independent — replace ${{ github.sha }} "
                          "with a hashFiles() of the file that invalidates it")
        else:
            report.manual(META.id, f"caches: {cache}",
                          "unknown cache name — add an actions/cache step with its path and key")
            continue
        job.setdefault("_pre_steps", []).append(
            {"uses": "actions/cache@v4",
             "with": {"path": path, "key": key_expr,
                      "restore-keys": "${{ runner.os }}-%s-" % cache}})
