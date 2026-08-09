"""when — stage conditions. Consumed by stages.py via to_if()."""

from portover.core import MappingMeta
from portover.migrations.jenkins_to_gha.parser import call_arg, kwargs

SCOPE = "stage"  # dispatched from stages.py, not the pipeline driver

META = MappingMeta(
    id="when",
    directive="when { branch / tag / changeRequest / environment / expression }",
    title="Migrate Jenkins when conditions to GitHub Actions if:",
    before="when { branch 'main' }",
    after="if: github.ref == 'refs/heads/main'",
    notes=(
        "branch -> github.ref, tag -> startsWith(github.ref, 'refs/tags/'), "
        "changeRequest() -> github.event_name == 'pull_request', environment "
        "name/value -> env comparison. `expression { }` is Groovy — rewrite the "
        "logic in GHA expression syntax by hand (flagged)."
    ),
    priority=45,
)


def matches(node) -> bool:
    return node.keyword() == "when"


def to_if(node, report) -> str | None:
    conds: list[str] = []
    items = list(node.stmts) + [c for c in node.children]
    for it in items:
        header = it if isinstance(it, str) else it.header
        kind = header.split("(")[0].split()[0]
        if kind == "branch":
            conds.append(f"github.ref == 'refs/heads/{call_arg(header)}'")
            report.mapped(META.id, header)
        elif kind == "tag":
            arg = call_arg(header)
            conds.append("startsWith(github.ref, 'refs/tags/')" if not arg or "*" in arg
                         else f"github.ref == 'refs/tags/{arg}'")
            report.mapped(META.id, header)
        elif kind == "changeRequest":
            conds.append("github.event_name == 'pull_request'")
            report.mapped(META.id, header)
        elif kind == "environment":
            kw = kwargs(header)
            conds.append(f"env.{kw.get('name', 'VAR')} == '{kw.get('value', '')}'")
            report.mapped(META.id, header)
        elif kind in ("expression", "not", "anyOf", "allOf"):
            report.manual(META.id, header, f"`{kind}` condition — rewrite in ${{{{ }}}} expression syntax by hand")
        else:
            report.manual(META.id, header, f"when condition '{kind}' not mapped")
    return " && ".join(conds) if conds else None
