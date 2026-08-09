"""coverage — the coverage-parsing regex."""

from portover.core import MappingMeta

SCOPE = "job"

META = MappingMeta(
    id="coverage",
    directive="coverage: /regex/",
    title="Migrate GitLab CI coverage regex to GitHub Actions",
    before="coverage: '/TOTAL.*\\s+(\\d+%)$/'",
    after="""# no built-in coverage parsing; either:
- run: pytest --cov --cov-report=xml
- uses: irongut/CodeCoverageSummary@v1.3.0
  with:
    filename: coverage.xml""",
    notes=(
        "GitLab scrapes the job log with this regex and shows the number on "
        "the MR and in badges. GHA has no log-scraping equivalent, so coverage "
        "moves to a report file plus an action (or a service like Codecov). "
        "The practical consequence is that the regex is dead weight — what you "
        "need instead is a `--cov-report=xml`-style flag on the test command."
    ),
    manual=True,
    priority=50,
)


def matches(key) -> bool:
    return key == "coverage"


def apply(key, value, job, ctx, report) -> None:
    report.manual(META.id, f"coverage: {value}",
                  "no log-scraping in GHA — emit a coverage report file and add a coverage action "
                  "(irongut/CodeCoverageSummary, or Codecov) instead")
