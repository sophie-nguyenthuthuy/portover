"""Just-enough YAML reader for .travis.yml files (keeps portover stdlib-only).

Covers what real Travis configs use: nested mappings, block and flow lists,
quoted scalars, comments, lists indented at the same level as their key.
Anchors, aliases, and block scalars raise MiniYamlError so the driver can
flag the file for manual handling instead of guessing.

Deliberate quirk: float-looking scalars stay strings — YAML would read
`python: 3.10` as 3.1, which is exactly the bug a Travis migrator can't have.
"""

from __future__ import annotations

import re


class MiniYamlError(ValueError):
    pass


_KEY = re.compile(r"^([A-Za-z0-9_.\-/*\" ']+):(\s+.*|)$")


def parse(text: str):
    rows = []
    for raw in text.splitlines():
        line = _strip_comment(raw.rstrip())
        if not line.strip():
            continue
        if line.lstrip().startswith("---"):
            continue
        rows.append((len(line) - len(line.lstrip()), line.strip()))
    if not rows:
        return {}
    value, pos = _block(rows, 0)
    if pos != len(rows):
        raise MiniYamlError(f"could not parse near: {rows[pos][1]!r}")
    return value


def _strip_comment(line: str) -> str:
    quote = None
    for i, ch in enumerate(line):
        if quote:
            if ch == quote:
                quote = None
        elif ch in "'\"":
            quote = ch
        elif ch == "#" and (i == 0 or line[i - 1] in " \t"):
            return line[:i]
    return line


def _block(rows, pos):
    indent = rows[pos][0]
    if rows[pos][1] == "-" or rows[pos][1].startswith("- "):
        return _sequence(rows, pos, indent)
    return _mapping(rows, pos, indent)


def _sequence(rows, pos, indent):
    items = []
    while pos < len(rows) and rows[pos][0] == indent and (rows[pos][1] == "-" or rows[pos][1].startswith("- ")):
        content = rows[pos][1][1:].strip()
        if not content:  # bare "-": nested block follows
            pos += 1
            if pos >= len(rows) or rows[pos][0] <= indent:
                items.append(None)
                continue
            val, pos = _block(rows, pos)
            items.append(val)
        elif _KEY.match(content):  # "- key: ..." starts an inline map item
            rows[pos] = (indent + 2, content)
            val, pos = _mapping(rows, pos, indent + 2)
            items.append(val)
        else:
            items.append(_scalar(content))
            pos += 1
    return items, pos


def _mapping(rows, pos, indent):
    out = {}
    while pos < len(rows) and rows[pos][0] == indent:
        m = _KEY.match(rows[pos][1])
        if not m:
            if not out:  # a lone scalar block
                return _scalar(rows[pos][1]), pos + 1
            break
        key = m.group(1).strip().strip("'\"")  # keys stay strings: `on:` must not become True
        rest = m.group(2).strip()
        pos += 1
        if rest:
            out[key] = _scalar(rest)
        elif pos < len(rows) and rows[pos][0] > indent:
            out[key], pos = _block(rows, pos)
        elif pos < len(rows) and rows[pos][0] == indent and (rows[pos][1] == "-" or rows[pos][1].startswith("- ")):
            out[key], pos = _sequence(rows, pos, indent)  # list at key's own indent
        else:
            out[key] = None
    return out, pos


def _scalar(s: str):
    s = s.strip()
    if s and s[0] in "&*|>":
        raise MiniYamlError(f"anchors/aliases/block scalars unsupported: {s!r}")
    if s.startswith("[") and s.endswith("]"):
        inner = s[1:-1].strip()
        return [_scalar(p) for p in _split_flow(inner)] if inner else []
    if len(s) >= 2 and s[0] in "'\"" and s.endswith(s[0]):
        return s[1:-1]
    low = s.lower()
    if low in ("true", "yes", "on"):
        return True
    if low in ("false", "no", "off"):
        return False
    if low in ("null", "~", ""):
        return None
    try:
        return int(s)
    except ValueError:
        return s  # floats intentionally stay strings ("3.10" != 3.1)


def _split_flow(inner: str):
    parts, buf, quote = [], "", None
    for ch in inner:
        if quote:
            buf += ch
            if ch == quote:
                quote = None
        elif ch in "'\"":
            quote = ch
            buf += ch
        elif ch == ",":
            parts.append(buf)
            buf = ""
        else:
            buf += ch
    if buf.strip():
        parts.append(buf)
    return parts
