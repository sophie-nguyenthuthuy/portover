"""store_artifacts/store_test_results — upload workflow artifacts."""

from portover.core import MappingMeta

SCOPE = "step"

META = MappingMeta(
    id="artifacts", directive="- store_artifacts / store_test_results",
    title="Migrate CircleCI artifacts and test results",
    before="""- store_artifacts:
    path: coverage
- store_test_results:
    path: test-results""",
    after="""- uses: actions/upload-artifact@v4
  with:
    name: coverage
    path: coverage""",
    notes="GHA stores test results as ordinary artifacts; add a reporting action if you want annotations and a test summary.",
    priority=30,
)


def matches(name) -> bool:
    return name in ("store_artifacts", "store_test_results")


def apply(name, value, out, ctx, report) -> None:
    spec = value if isinstance(value, dict) else {"path": value}
    path = str(spec.get("path", "."))
    artifact_name = str(spec.get("destination") or ("test-results" if name == "store_test_results" else path.rstrip("/").split("/")[-1]))
    out.append({"uses": "actions/upload-artifact@v4", "with": {"name": artifact_name, "path": path}})
    report.mapped(META.id, name, f"upload-artifact: {artifact_name}")
