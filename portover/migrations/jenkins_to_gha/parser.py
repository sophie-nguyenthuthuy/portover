"""Just-enough parser for declarative Jenkinsfiles.

Produces a tree of Node(header, children, stmts). Not a Groovy parser — it
tracks quotes/comments/braces and treats everything between them as opaque
statements, which is all the mappings need.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Node:
    header: str  # e.g. "pipeline", "stage('Build')", "agent any" for bare stmts
    children: list["Node"] = field(default_factory=list)
    stmts: list[str] = field(default_factory=list)

    def child(self, keyword: str) -> "Node | None":
        for c in self.children:
            if c.header == keyword or c.header.startswith(keyword + "(") or c.header.startswith(keyword + " "):
                return c
        return None

    def keyword(self) -> str:
        return self.header.split("(")[0].split()[0] if self.header.strip() else ""


def strip_comments(text: str) -> str:
    out, i, n = [], 0, len(text)
    while i < n:
        c = text[i]
        if c in "'\"":
            q = text[i : i + 3] if text[i : i + 3] in ("'''", '"""') else c
            end = text.find(q, i + len(q))
            end = n if end == -1 else end + len(q)
            out.append(text[i:end])
            i = end
        elif text.startswith("//", i):
            i = text.find("\n", i)
            i = n if i == -1 else i
        elif text.startswith("/*", i):
            j = text.find("*/", i + 2)
            i = n if j == -1 else j + 2
        else:
            out.append(c)
            i += 1
    return "".join(out)


def parse(text: str) -> Node:
    """Parse to a root Node whose children/stmts are the top-level items."""
    text = strip_comments(text)
    root = Node("")
    stack = [root]
    buf = ""
    i, n = 0, len(text)
    depth_paren = 0
    while i < n:
        c = text[i]
        if c in "'\"":
            q = text[i : i + 3] if text[i : i + 3] in ("'''", '"""') else c
            end = text.find(q, i + len(q))
            end = n if end == -1 else end + len(q)
            buf += text[i:end]
            i = end
            continue
        if c == "(":
            depth_paren += 1
        elif c == ")":
            depth_paren -= 1
        if c == "{" and depth_paren == 0:
            node = Node(buf.strip())
            stack[-1].children.append(node)
            stack.append(node)
            buf = ""
        elif c == "}" and depth_paren == 0:
            _flush(stack[-1], buf)
            buf = ""
            if len(stack) > 1:
                stack.pop()
        elif c in "\n;" and depth_paren == 0:
            _flush(stack[-1], buf)
            buf = ""
        else:
            buf += c
        i += 1
    _flush(root, buf)
    return root


def _flush(node: Node, buf: str) -> None:
    stmt = buf.strip()
    if stmt:
        node.stmts.append(stmt)


def unquote(s: str) -> str:
    s = s.strip()
    for q in ("'''", '"""', "'", '"'):
        if s.startswith(q) and s.endswith(q) and len(s) >= 2 * len(q):
            return s[len(q) : -len(q)]
    return s


def call_arg(stmt: str) -> str:
    """First string argument of `sh 'x'` / `sh("x")` / `cron('H * * * *')` styles."""
    rest = stmt.split("(", 1)[1].rsplit(")", 1)[0] if "(" in stmt else stmt.split(None, 1)[1] if " " in stmt else ""
    return unquote(rest.split(",")[0] if rest.startswith(("'", '"')) and "," in rest else rest)


def kwargs(stmt: str) -> dict[str, str]:
    """Parse `name: 'x', defaultValue: 'y'` style keyword args inside a call."""
    inner = stmt.split("(", 1)[1].rsplit(")", 1)[0] if "(" in stmt else ""
    out: dict[str, str] = {}
    depth = 0
    part = ""
    parts = []
    for ch in inner:
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append(part)
            part = ""
        else:
            part += ch
    if part.strip():
        parts.append(part)
    for p in parts:
        if ":" in p:
            k, _, v = p.partition(":")
            out[k.strip()] = unquote(v)
    return out
