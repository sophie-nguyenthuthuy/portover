"""only / except — the legacy per-job filters."""

from portover.core import MappingMeta

SCOPE = "job"

META = MappingMeta(
    id="only-except",
    directive="only: / except:",
    title="Migrate GitLab CI only and except to GitHub Actions",
    before="""only:
  - main
  - /^release-.*$/
except:
  - schedules""",
    after="""if: >-
  (github.ref_name == 'main' || startsWith(github.ref_name, 'release-'))
  && !(github.event_name == 'schedule')""",
    notes=(
        "`only`/`except` are the superseded form of `rules:` — GitLab still "
        "accepts them but you cannot mix the two in one job. Bare names are "
        "matched against refs, `/regex/` entries become startsWith/contains, and "
        "the keywords (branches, tags, merge_requests, schedules, api, web) map "
        "to GHA event names. Refs and keywords in one list are ORed, matching "
        "GitLab."
    ),
    priority=22,
)

_KEYWORDS = {
    "branches": "github.ref_type == 'branch'",
    "tags": "github.ref_type == 'tag'",
    "merge_requests": "github.event_name == 'pull_request'",
    "schedules": "github.event_name == 'schedule'",
    "api": "github.event_name == 'workflow_dispatch'",
    "web": "github.event_name == 'workflow_dispatch'",
    "pushes": "github.event_name == 'push'",
    "external_pull_requests": "github.event_name == 'pull_request'",
}


def matches(key) -> bool:
    return key in ("only", "except")


def apply(key, value, job, ctx, report) -> None:
    from portover.migrations.gitlab_ci_to_gha import as_list

    if isinstance(value, dict):
        for unsupported in set(value) - {"refs"}:
            report.manual(META.id, f"{key}.{unsupported}",
                          "only/except sub-keys (changes, kubernetes, variables) have no direct "
                          "equivalent — use rules: semantics or dorny/paths-filter")
        entries = as_list(value.get("refs"))
    else:
        entries = as_list(value)

    conditions = []
    for entry in entries:
        text = str(entry)
        if text in _KEYWORDS:
            conditions.append(_KEYWORDS[text])
            report.mapped(META.id, f"{key}: {text}", _KEYWORDS[text])
        elif text.startswith("/") and text.endswith("/"):
            body = text.strip("/")
            literal = body.removeprefix("^").split(".*")[0].rstrip("$")
            if not literal:
                report.manual(META.id, f"{key}: {text}", "regex has no literal prefix — write the condition by hand")
                continue
            rendered = (f"startsWith(github.ref_name, '{literal}')" if body.startswith("^")
                        else f"contains(github.ref_name, '{literal}')")
            conditions.append(rendered)
            report.mapped(META.id, f"{key}: {text}", rendered)
        else:
            conditions.append(f"github.ref_name == '{text}'")
            report.mapped(META.id, f"{key}: {text}")

    if not conditions:
        return
    joined = conditions[0] if len(conditions) == 1 else "(" + " || ".join(conditions) + ")"
    if key == "except":
        joined = f"!{joined}" if joined.startswith("(") else f"!({joined})"
    job["if"] = f"{job['if']} && {joined}" if job.get("if") else joined
