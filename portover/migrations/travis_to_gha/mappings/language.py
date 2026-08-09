"""language + version lists (python:, node_js:, go:) -> setup actions + matrix."""

from portover.core import MappingMeta

META = MappingMeta(
    id="language",
    directive="language / python / node_js / go",
    title="Migrate Travis language and version matrix to GitHub Actions",
    before='language: python\npython:\n  - "3.11"\n  - "3.12"',
    after="""strategy:
  matrix:
    python: ["3.11", "3.12"]
steps:
  - uses: actions/setup-python@v5
    with:
      python-version: ${{ matrix.python }}""",
    notes=(
        "One version -> plain setup step; several -> a matrix dimension named "
        "after the language. GHA runners preinstall many runtimes, but pinning "
        "via setup-* keeps the version explicit like Travis did."
    ),
    priority=10,
)

_SETUP = {
    "python": ("actions/setup-python@v5", "python-version"),
    "node_js": ("actions/setup-node@v4", "node-version"),
    "go": ("actions/setup-go@v5", "go-version"),
    "ruby": ("ruby/setup-ruby@v1", "ruby-version"),
    "java": ("actions/setup-java@v4", "java-version"),
    "jdk": ("actions/setup-java@v4", "java-version"),
}
_MATRIX_KEY = {"node_js": "node", "jdk": "java"}


def matches(key) -> bool:
    return key == "language" or key in _SETUP


def apply(key, value, ctx, report) -> None:
    if key == "language":
        ctx.language = str(value)
        report.mapped(META.id, f"language: {value}")
        return
    action, with_key = _SETUP[key]
    versions = [str(v) for v in (value if isinstance(value, list) else [value])]
    mkey = _MATRIX_KEY.get(key, key)
    step = {"uses": action, "with": {with_key: versions[0]}}
    if len(versions) > 1:
        ctx.matrix[mkey] = versions
        step["with"][with_key] = "${{ matrix.%s }}" % mkey
    if action == "actions/setup-java@v4":
        step["with"] = {"distribution": "temurin", **step["with"]}
    ctx.setup_steps.append(step)
    report.mapped(META.id, f"{key}: {versions}",
                  f"{action}" + (f" + matrix.{mkey}" if len(versions) > 1 else ""))
