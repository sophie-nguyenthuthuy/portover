# Contributing to portover

The contributor unit is **one mapping for one directive**. You don't need to
understand the whole codebase — you need to know what one Jenkins directive
(or pip flag, or flake8 key) becomes on the other side, because you just
migrated it by hand and the tool didn't cover it.

## Add a mapping (~40 lines, one file)

1. Pick the migration, e.g. `portover/migrations/jenkins_to_gha/`.
2. Drop a new file in its `mappings/` folder. Existing = registered; there is
   no list to edit.

```python
"""retry — retry a stage on failure."""

from portover.core import MappingMeta

SCOPE = "step"  # jenkins-to-gha only: "pipeline" or "step"

META = MappingMeta(
    id="retry",
    directive="retry(3) { ... }",
    title="Migrate Jenkins retry to GitHub Actions",
    before="retry(3) { sh './flaky.sh' }",
    after="- uses: nick-fields/retry@v3\n  with: { max_attempts: 3, command: ./flaky.sh }",
    notes="No built-in retry in GHA; nick-fields/retry is the standard action.",
    priority=20,  # lower runs first; generic fallbacks go high
)

def matches(stmt):        # is this yours?
    return stmt.startswith("retry(")

def apply(stmt, steps, ctx, report):   # convert it — or flag it
    ...
    report.mapped(META.id, stmt)       # or report.manual(META.id, stmt, "how to do it by hand")
```

3. Add a test next to the others in `tests/` (input snippet in, expected output
   or manual flag out).
4. `pip install pytest pyyaml` (pyyaml is test-only — the tests check the
   generated YAML with a real parser; portover itself has zero dependencies),
   then `python -m pytest` and `python -m portover.cli docs` — your doc page in
   `docs/` is generated from `META`, no docs to write.

Rules of the house:

- **Never silently drop a directive.** If it can't be converted, `report.manual()`
  with instructions beats guessing.
- `META.before`/`META.after` must be real, copy-pasteable snippets — they are
  the doc page someone finds from a search engine.
- One directive per file. If your mapping handles two things, it's two files.

## Add a whole migration

A migration is a folder with a driver (`__init__.py`: `detect()` + `run()`,
subclassing `portover.core.Migration`) and a `mappings/` package. Register it
in `portover/migrations/__init__.py` (the one place a list is edited). Start by
copying `flake8_to_ruff/` — it's the smallest — and look at an existing driver
for the report/output conventions. Ideas wanted: Drone→GHA, TeamCity→GHA, Woodpecker→GHA,
setup.py→pyproject, Makefile→just, tox→nox, Dockerfile→Containerfile quirks…
