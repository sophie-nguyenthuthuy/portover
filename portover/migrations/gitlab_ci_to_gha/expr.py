"""Translate GitLab CI rule expressions into GitHub Actions expressions.

GitLab writes conditions against shell-style variables (`$CI_COMMIT_BRANCH ==
"main"`); GHA writes them against contexts (`github.ref_name == 'main'`). This
module does that swap for the predefined variables people actually branch on,
leaves user-defined variables as `env.NAME`, and reports anything it cannot
translate rather than emitting a condition that silently means something else.
"""

from __future__ import annotations

import re

# GitLab predefined variable -> GHA expression fragment (no ${{ }} wrapper)
CONTEXT = {
    "CI_COMMIT_BRANCH": "github.ref_name",
    "CI_COMMIT_REF_NAME": "github.ref_name",
    "CI_COMMIT_REF_SLUG": "github.ref_name",
    "CI_DEFAULT_BRANCH": "github.event.repository.default_branch",
    "CI_COMMIT_SHA": "github.sha",
    "CI_COMMIT_TAG": "github.ref_name",
    "CI_PROJECT_PATH": "github.repository",
    "CI_PROJECT_NAME": "github.event.repository.name",
    "CI_PIPELINE_ID": "github.run_id",
    "CI_JOB_NAME": "github.job",
    "CI_MERGE_REQUEST_TARGET_BRANCH_NAME": "github.base_ref",
    "CI_MERGE_REQUEST_SOURCE_BRANCH_NAME": "github.head_ref",
}

# $CI_PIPELINE_SOURCE == "x" -> github.event_name == 'y'
PIPELINE_SOURCE = {
    "merge_request_event": "pull_request",
    "push": "push",
    "schedule": "schedule",
    "web": "workflow_dispatch",
    "api": "workflow_dispatch",
    "trigger": "repository_dispatch",
    "pipeline": "workflow_call",
}

_VAR = re.compile(r"\$\{?([A-Za-z_][A-Za-z0-9_]*)\}?")
_CLAUSE = re.compile(
    r"""^\s*(?P<lhs>\$\{?[A-Za-z_][A-Za-z0-9_]*\}?)\s*
        (?:(?P<op>==|!=|=~|!~)\s*(?P<rhs>"[^"]*"|'[^']*'|/.*/[a-z]*|\$\{?[A-Za-z_][A-Za-z0-9_]*\}?))?\s*$""",
    re.VERBOSE,
)


def translate(expression: str, report=None, mapping_id: str = "rules") -> str | None:
    """Translate one GitLab `if:` expression. Returns None if untranslatable."""
    text = str(expression).strip()
    parts = _split_logical(text)
    out = []
    for joiner, clause in parts:
        piece = _clause(clause)
        if piece is None:
            if report is not None:
                report.manual(mapping_id, f"if: {text}",
                              f"could not translate `{clause.strip()}` — write this condition by hand")
            return None
        out.append((joiner, piece))
    rendered = out[0][1]
    for joiner, piece in out[1:]:
        rendered += f" {joiner} {piece}"
    return rendered


def _split_logical(text: str):
    """Split on && / || at paren depth 0, keeping the joiner."""
    parts, buf, depth, joiner, quote = [], "", 0, "", None
    i = 0
    while i < len(text):
        ch = text[i]
        if quote:
            buf += ch
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
            buf += ch
        elif ch in "([":
            depth += 1
            buf += ch
        elif ch in ")]":
            depth -= 1
            buf += ch
        elif depth == 0 and text[i:i + 2] in ("&&", "||"):
            parts.append((joiner, buf))
            joiner = text[i:i + 2]
            buf = ""
            i += 2
            continue
        else:
            buf += ch
        i += 1
    parts.append((joiner, buf))
    return parts


def _clause(clause: str) -> str | None:
    text = clause.strip()
    negate = False
    while text.startswith("!") and not text.startswith("!~"):
        negate = not negate
        text = text[1:].strip()
    text = text.strip("()").strip() if text.startswith("(") and text.endswith(")") else text

    m = _CLAUSE.match(text)
    if not m:
        return None
    name = _VAR.match(m.group("lhs")).group(1)
    op, rhs = m.group("op"), m.group("rhs")

    if op is None:  # bare truthiness: $CI_COMMIT_TAG
        rendered = _truthy(name)
        return _neg(rendered, negate) if rendered else None

    if name == "CI_PIPELINE_SOURCE" and op in ("==", "!="):
        source = PIPELINE_SOURCE.get(_unquote(rhs))
        if source is None:
            return None
        return _neg(f"github.event_name {op} '{source}'", negate)

    lhs = CONTEXT.get(name, f"env.{name}")
    if op in ("=~", "!~"):
        pattern = _unquote(rhs)
        if not (pattern.startswith("/") and pattern.rstrip("a-z").endswith("/")):
            return None
        body = pattern.strip("/")
        literal = body.removeprefix("^").split(".*")[0].split("[")[0].split("(")[0].rstrip("$")
        if not literal or any(c in literal for c in "\\|+?{"):
            return None
        rendered = (f"startsWith({lhs}, '{literal}')" if body.startswith("^")
                    else f"contains({lhs}, '{literal}')")
        return _neg(rendered, op == "!~" and not negate or negate and op == "=~")

    if rhs.startswith("$"):
        rhs_name = _VAR.match(rhs).group(1)
        right = CONTEXT.get(rhs_name, f"env.{rhs_name}")
    else:
        right = f"'{_unquote(rhs)}'"
    return _neg(f"{lhs} {op} {right}", negate)


def _truthy(name: str) -> str | None:
    if name == "CI_COMMIT_TAG":
        return "github.ref_type == 'tag'"
    if name in ("CI_MERGE_REQUEST_IID", "CI_MERGE_REQUEST_ID"):
        return "github.event_name == 'pull_request'"
    if name in CONTEXT:
        return f"{CONTEXT[name]} != ''"
    return f"env.{name} != ''"


def _neg(rendered: str, negate: bool) -> str:
    return f"!({rendered})" if negate else rendered


def _unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] in "\"'" and value[-1] == value[0]:
        return value[1:-1]
    return value
