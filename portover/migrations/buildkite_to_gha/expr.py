"""Translate Buildkite `if:` expressions into GitHub Actions expressions.

Buildkite's condition language is already infix, so this is closer to a
substitution than the Azure parser — but the operands differ in kind, not just
name: `build.tag == null` is a statement about the ref TYPE in GHA, and
`build.pull_request.id != null` is a statement about the EVENT. Those are
special-cased; anything left untranslatable returns None and is reported.
"""

from __future__ import annotations

import re

OPERANDS = {
    "build.branch": "github.ref_name",
    "build.commit": "github.sha",
    "build.message": "github.event.head_commit.message",
    "build.number": "github.run_number",
    "build.source": "github.event_name",
    "build.creator.name": "github.actor",
    "build.creator.email": "github.actor",
    "build.pull_request.base_branch": "github.base_ref",
    "build.pull_request.repository": "github.event.pull_request.head.repo.full_name",
    "build.pull_request.draft": "github.event.pull_request.draft",
    "pipeline.slug": "github.workflow",
    "pipeline.default_branch": "github.event.repository.default_branch",
    "organization.slug": "github.repository_owner",
}

# build.source values -> github.event_name values
SOURCES = {
    "webhook": "push",
    "local": "push",
    "ui": "workflow_dispatch",
    "api": "workflow_dispatch",
    "schedule": "schedule",
    "trigger_job": "workflow_call",
}

_ENV_CALL = re.compile(r"""build\.env\(\s*['"]([A-Za-z_][A-Za-z0-9_]*)['"]\s*\)""")
_CLAUSE = re.compile(
    r"""^\s*(?P<lhs>[A-Za-z_][A-Za-z0-9_.]*(?:\(\s*['"][^'"]*['"]\s*\))?)\s*
        (?:(?P<op>==|!=|=~|!~)\s*(?P<rhs>"[^"]*"|'[^']*'|/[^/]*/[a-z]*|null|true|false|\d+))?\s*$""",
    re.VERBOSE,
)


def translate(expression, report=None, mapping_id: str = "if") -> str | None:
    text = str(expression).strip()
    if not text:
        return None
    parts = _split_logical(text)
    rendered = []
    for joiner, clause in parts:
        piece = _clause(clause)
        if piece is None:
            if report is not None:
                report.manual(mapping_id, f"if: {text}",
                              f"could not translate `{clause.strip()}` — write the condition by hand")
            return None
        rendered.append((joiner, piece))
    out = rendered[0][1]
    for joiner, piece in rendered[1:]:
        out += f" {joiner} {piece}"
    return out


def _split_logical(text: str):
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
        elif ch == "/" and not quote and buf.rstrip().endswith(("=~", "!~")):
            end = text.find("/", i + 1)
            end = len(text) if end == -1 else end + 1
            buf += text[i:end]
            i = end
            continue
        elif ch == "(":
            depth += 1
            buf += ch
        elif ch == ")":
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
    if text.startswith("(") and text.endswith(")"):
        inner = translate(text[1:-1])
        return _neg(f"({inner})", negate) if inner else None

    m = _CLAUSE.match(text)
    if not m:
        return None
    lhs_raw, op, rhs = m.group("lhs"), m.group("op"), m.group("rhs")

    special = _special(lhs_raw, op, rhs)
    if special is not None:
        return _neg(special, negate)

    lhs = _operand(lhs_raw)
    if lhs is None:
        return None
    if op is None:
        return _neg(f"{lhs} != ''", negate)
    if op in ("=~", "!~"):
        rendered = _regex(lhs, rhs)
        if rendered is None:
            return None
        return _neg(rendered, negate if op == "=~" else not negate)
    if rhs == "null":
        return _neg(f"{lhs} {'==' if op == '==' else '!='} ''", negate)
    if rhs in ("true", "false"):
        return _neg(f"{lhs} {op} {rhs}", negate)
    value = rhs.strip("\"'")
    if lhs == "github.event_name":
        value = SOURCES.get(value, value)
    return _neg(f"{lhs} {op} '{value}'", negate)


def _special(lhs: str, op, rhs) -> str | None:
    """Operands whose GHA equivalent is a different kind of statement."""
    if lhs == "build.tag":
        if rhs == "null":
            return "github.ref_type != 'tag'" if op == "==" else "github.ref_type == 'tag'"
        if op is None:
            return "github.ref_type == 'tag'"
        if op in ("==", "!=") and rhs:
            return f"github.ref_name {op} '{rhs.strip(chr(34) + chr(39))}'"
        if op == "=~":
            return _regex("github.ref_name", rhs)
    if lhs in ("build.pull_request.id", "build.pull_request.number"):
        if rhs == "null":
            return ("github.event_name != 'pull_request'" if op == "=="
                    else "github.event_name == 'pull_request'")
        if op is None:
            return "github.event_name == 'pull_request'"
    return None


def _operand(raw: str) -> str | None:
    env = _ENV_CALL.match(raw)
    if env:
        return f"env.{env.group(1)}"
    return OPERANDS.get(raw)


def _regex(lhs: str, rhs) -> str | None:
    if not rhs or not rhs.startswith("/"):
        return None
    body = rhs.strip("/").rstrip("i")
    anchored = body.startswith("^")
    literal = body.removeprefix("^").rstrip("$").split(".*")[0].split("[")[0].split("(")[0]
    if not literal or any(c in literal for c in "\\|+?{"):
        return None
    return f"startsWith({lhs}, '{literal}')" if anchored else f"contains({lhs}, '{literal}')"


def _neg(rendered: str, negate: bool) -> str:
    return f"!({rendered})" if negate else rendered
