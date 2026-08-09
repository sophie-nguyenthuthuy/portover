"""Translate Azure Pipelines conditions into GitHub Actions expressions.

Azure writes conditions in prefix function form —
``and(succeeded(), eq(variables['Build.SourceBranch'], 'refs/heads/main'))`` —
while GHA uses infix operators. That is a real (if small) language, so this is
a recursive-descent parser rather than a pile of regexes: anything it cannot
parse returns None and gets reported, instead of being half-rewritten into a
condition that quietly means something else.
"""

from __future__ import annotations

import re

# Azure predefined variable -> GHA expression
VARIABLES = {
    "build.sourcebranch": "github.ref",
    "build.sourcebranchname": "github.ref_name",
    "build.sourceversion": "github.sha",
    "build.repository.name": "github.repository",
    "build.buildid": "github.run_id",
    "build.buildnumber": "github.run_number",
    "build.requestedfor": "github.actor",
    "build.definitionname": "github.workflow",
    "system.defaultworkingdirectory": "github.workspace",
    "system.pullrequest.pullrequestid": "github.event.pull_request.number",
    "system.pullrequest.sourcebranch": "github.head_ref",
    "system.pullrequest.targetbranch": "github.base_ref",
    "agent.os": "runner.os",
}

# Build.Reason values -> github.event_name values
REASONS = {
    "pullrequest": "pull_request",
    "individualci": "push",
    "batchedci": "push",
    "schedule": "schedule",
    "manual": "workflow_dispatch",
    "resourcetrigger": "repository_dispatch",
}

_STATUS = {
    "succeeded": "success()",
    "failed": "failure()",
    "always": "always()",
    "canceled": "cancelled()",
    "cancelled": "cancelled()",
    "succeededorfailed": "always()",
}

_INFIX = {"eq": "==", "ne": "!=", "lt": "<", "le": "<=", "gt": ">", "ge": ">="}
_PASSTHROUGH = {"startswith": "startsWith", "endswith": "endsWith", "contains": "contains"}

_TOKEN = re.compile(r"""\s*(?P<tok>
      '(?:[^']|'')*'          # single-quoted string
    | \[\s*'(?:[^']|'')*'\s*\] # ['index']
    | [A-Za-z_][A-Za-z0-9_.]* # identifier / variable path
    | \d+
    | [(),]
    )""", re.VERBOSE)


class _Parser:
    def __init__(self, text: str):
        self.tokens = self._lex(text)
        self.pos = 0

    def _lex(self, text: str):
        tokens, i = [], 0
        while i < len(text):
            m = _TOKEN.match(text, i)
            if not m:
                if text[i].isspace():
                    i += 1
                    continue
                raise ValueError(f"unexpected character {text[i]!r}")
            tokens.append(m.group("tok"))
            i = m.end()
        return tokens

    def peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def next(self):
        tok = self.peek()
        self.pos += 1
        return tok

    def parse(self) -> str:
        value = self.expression()
        if self.peek() is not None:
            raise ValueError(f"trailing input at {self.peek()!r}")
        return value

    def expression(self) -> str:
        tok = self.next()
        if tok is None:
            raise ValueError("empty expression")
        if tok.startswith("'"):
            return "'" + tok[1:-1].replace("''", "'") + "'"
        if tok.isdigit():
            return tok
        if tok == "(":  # parenthesised group is not Azure syntax, but be lenient
            inner = self.expression()
            if self.next() != ")":
                raise ValueError("unbalanced parenthesis")
            return f"({inner})"

        name = tok.lower()
        if self.peek() == "(":
            self.next()
            args = []
            if self.peek() != ")":
                while True:
                    args.append(self.expression())
                    nxt = self.next()
                    if nxt == ")":
                        break
                    if nxt != ",":
                        raise ValueError(f"expected , or ) but found {nxt!r}")
            else:
                self.next()
            return self.call(name, args)

        if name == "variables":  # variables['X'] or variables.X
            return self.variable_index()
        if name in ("true", "false"):
            return name
        return _variable(tok)

    def variable_index(self) -> str:
        tok = self.peek()
        if tok and tok.startswith("["):
            self.next()
            inner = tok.strip("[]").strip()
            return _variable(inner.strip("'").replace("''", "'"))
        raise ValueError("expected variables['name']")

    def call(self, name: str, args: list) -> str:
        if name in _STATUS:
            return _STATUS[name]
        if name == "not" and len(args) == 1:
            return f"!({args[0]})"
        if name in ("and", "or") and args:
            joiner = " && " if name == "and" else " || "
            return joiner.join(args) if len(args) == 1 else "(" + joiner.join(args) + ")"
        if name in _INFIX and len(args) == 2:
            left, right = _reason_pair(args[0], args[1])
            return f"{left} {_INFIX[name]} {right}"
        if name in _PASSTHROUGH and len(args) >= 2:
            return f"{_PASSTHROUGH[name]}({args[0]}, {args[1]})"
        if name == "in" and len(args) >= 2:
            return "(" + " || ".join(f"{args[0]} == {a}" for a in args[1:]) + ")"
        if name == "notin" and len(args) >= 2:
            return "!(" + " || ".join(f"{args[0]} == {a}" for a in args[1:]) + ")"
        if name == "coalesce" and args:
            return " || ".join(args)
        raise ValueError(f"unsupported function {name}()")


def _variable(path: str) -> str:
    key = path.strip().strip("'").lower()
    if key in VARIABLES:
        return VARIABLES[key]
    if key == "build.reason":
        return "github.event_name"
    safe = re.sub(r"[^A-Za-z0-9_]", "_", path.strip().strip("'"))
    return f"env.{safe}"


def _reason_pair(left: str, right: str):
    """eq(variables['Build.Reason'], 'PullRequest') -> event_name == 'pull_request'."""
    for a, b in ((left, right), (right, left)):
        if a == "github.event_name" and b.startswith("'"):
            mapped = REASONS.get(b.strip("'").lower())
            if mapped:
                return (a, f"'{mapped}'") if a is left else (f"'{mapped}'", a)
    return left, right


def translate(condition, report=None, mapping_id: str = "condition") -> str | None:
    """Translate one Azure condition. Returns None (and reports) if unsupported."""
    text = str(condition).strip()
    if not text:
        return None
    text = re.sub(r"^\$\{\{\s*(.*?)\s*\}\}$", r"\1", text)  # ${{ }} compile-time wrapper
    try:
        return _Parser(text).parse()
    except (ValueError, IndexError) as e:
        if report is not None:
            report.manual(mapping_id, f"condition: {text}",
                          f"could not translate ({e}) — write the `if:` condition by hand")
        return None
