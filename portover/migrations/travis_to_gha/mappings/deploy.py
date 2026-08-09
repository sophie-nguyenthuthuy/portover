"""deploy — provider blocks."""

from portover.core import MappingMeta

META = MappingMeta(
    id="deploy",
    directive="deploy: provider: pypi / pages / script / releases ...",
    title="Migrate Travis deploy to GitHub Actions",
    before="deploy:\n  provider: pypi\n  username: __token__\n  on:\n    tags: true",
    after="""# separate job, gated on tags:
publish:
  if: startsWith(github.ref, 'refs/tags/')
  permissions: { id-token: write }
  steps:
    - uses: pypa/gh-action-pypi-publish@release/v1""",
    notes=(
        "Deployment is where 1:1 translation stops being a favor — each "
        "provider has a better native pattern: pypi -> trusted publishing "
        "(no token at all), pages -> actions/deploy-pages, releases -> "
        "softprops/action-gh-release, script -> a run step gated with "
        "`if: startsWith(github.ref, 'refs/tags/')`. portover flags the "
        "provider and points at the pattern instead of transplanting "
        "credentials."
    ),
    manual=True,
    priority=50,
)

_HINTS = {
    "pypi": "use PyPI trusted publishing: pypa/gh-action-pypi-publish with id-token: write (no token needed)",
    "pages": "use actions/upload-pages-artifact + actions/deploy-pages (or peaceiris/actions-gh-pages)",
    "releases": "use softprops/action-gh-release with the tag's files",
    "script": "run the script in a step gated with `if: startsWith(github.ref, 'refs/tags/')`",
    "npm": "use actions/setup-node with registry-url + `npm publish` and an NPM_TOKEN secret (or npm trusted publishing)",
    "heroku": "Heroku's git-push deploy works from a run step with a HEROKU_API_KEY secret",
    "s3": "use aws-actions/configure-aws-credentials (OIDC) + `aws s3 sync`",
}


def matches(key) -> bool:
    return key == "deploy"


def apply(key, value, ctx, report) -> None:
    blocks = value if isinstance(value, list) else [value]
    for block in blocks:
        provider = str(block.get("provider", "?")) if isinstance(block, dict) else str(block)
        hint = _HINTS.get(provider, "find the provider's official action on the GitHub marketplace")
        cond = ""
        if isinstance(block, dict) and isinstance(block.get("on"), dict):
            if block["on"].get("tags"):
                cond = " — gate it with `if: startsWith(github.ref, 'refs/tags/')`"
            elif block["on"].get("branch"):
                cond = f" — gate it with `if: github.ref == 'refs/heads/{block['on']['branch']}'`"
        report.manual(META.id, f"deploy.provider: {provider}", hint + cond)
