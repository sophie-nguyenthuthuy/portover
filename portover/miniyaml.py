"""Just-enough YAML reader, shared by the YAML-sourced migrations.

Keeps portover stdlib-only. Covers what real CI configs use: nested mappings,
block and flow sequences, lists of maps, quoted scalars, comments, and block
scalars (``|``, ``|-``, ``>``) — which is how nearly every CircleCI ``run``
command is written. Anchors and aliases raise MiniYamlError so a driver can
flag the file for manual handling instead of silently guessing.

Two deliberate departures from a real YAML loader, both bug-avoidance:

- Mapping *keys* stay strings, so Travis' ``on:`` does not become ``True``.
- Float-looking scalars stay strings, so ``python: 3.10`` does not become 3.1.
"""

from __future__ import annotations

import re


class MiniYamlError(ValueError):
    pass


_KEY = re.compile(r"^([A-Za-z0-9_.\-/*\"' ]+):(\s+.*|)$")
_BLOCK_HEADER = re.compile(r"^(.*?):\s*([|>])([-+]?)\d*\s*$")


def parse(text: str):
    rows = _rows(text)
    if not rows:
        return {}
    value, pos = _block(rows, 0)
    if pos != len(rows):
        raise MiniYamlError(f"could not parse near: {rows[pos][1]!r}")
    return value


def _rows(text: str):
    """Rows are (indent, text, literal); literal is the body of a block scalar."""
    out = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        raw = lines[i].rstrip()
        stripped_raw = raw.strip()
        if not stripped_raw or stripped_raw.startswith("#") or stripped_raw.startswith("---"):
            i += 1
            continue
        line = _strip_comment(raw)
        if not line.strip():
            i += 1
            continue
        indent = len(line) - len(line.lstrip())
        text_ = line.strip()
        m = _BLOCK_HEADER.match(text_)
        if m and not m.group(1).strip().endswith(("'", '"')):
            # For a sequence item (`- key: |`) the block body must out-indent the
            # KEY, not the dash — otherwise a sibling key of the same item gets
            # swallowed into the scalar.
            key_indent = indent + 2 if text_.startswith("- ") else indent
            body, i = _consume_block(lines, i + 1, key_indent, style=m.group(2), chomp=m.group(3))
            out.append((indent, m.group(1).strip() + ":", body))
            continue
        out.append((indent, text_, None))
        i += 1
    return out


def _consume_block(lines, i, header_indent, *, style, chomp):
    body, base = [], None
    while i < len(lines):
        raw = lines[i].rstrip("\n").rstrip()
        if raw.strip():
            indent = len(raw) - len(raw.lstrip())
            if indent <= header_indent:
                break
            if base is None:
                base = indent
            body.append(raw[base:] if len(raw) >= base else raw.lstrip())
        else:
            body.append("")
        i += 1
    while body and not body[-1].strip():
        body.pop()
    if style == ">":
        folded, buf = [], []
        for ln in body:
            if ln.strip():
                buf.append(ln.strip())
            else:
                folded.append(" ".join(buf))
                buf = []
        if buf:
            folded.append(" ".join(buf))
        body = folded
    value = "\n".join(body)
    if chomp != "-" and value:
        value += "\n"
    return value, i


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
        literal = rows[pos][2]
        if not content:  # bare "-": a nested block follows
            pos += 1
            if pos >= len(rows) or rows[pos][0] <= indent:
                items.append(None)
                continue
            val, pos = _block(rows, pos)
            items.append(val)
        elif _KEY.match(content):  # "- key: ..." opens an inline mapping item
            rows[pos] = (indent + 2, content, literal)
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
        literal = rows[pos][2]
        pos += 1
        if literal is not None:
            out[key] = literal
        elif rest:
            out[key] = _scalar(rest)
        elif pos < len(rows) and rows[pos][0] > indent:
            out[key], pos = _block(rows, pos)
        elif pos < len(rows) and rows[pos][0] == indent and (rows[pos][1] == "-" or rows[pos][1].startswith("- ")):
            out[key], pos = _sequence(rows, pos, indent)  # list at its key's own indent
        else:
            out[key] = None
    return out, pos


def _scalar(s: str):
    s = s.strip()
    if s and s[0] in "&*":
        raise MiniYamlError(f"anchors/aliases unsupported: {s!r}")
    if s.startswith("[") and s.endswith("]"):
        inner = s[1:-1].strip()
        return [_scalar(p) for p in _split_flow(inner)] if inner else []
    if s.startswith("{") and s.endswith("}"):
        inner = s[1:-1].strip()
        out = {}
        for part in _split_flow(inner):
            k, _, v = part.partition(":")
            out[k.strip().strip("'\"")] = _scalar(v)
        return out
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
    parts, buf, quote, depth = [], "", None, 0
    for ch in inner:
        if quote:
            buf += ch
            if ch == quote:
                quote = None
        elif ch in "'\"":
            quote = ch
            buf += ch
        elif ch in "[{":
            depth += 1
            buf += ch
        elif ch in "]}":
            depth -= 1
            buf += ch
        elif ch == "," and depth == 0:
            parts.append(buf)
            buf = ""
        else:
            buf += ch
    if buf.strip():
        parts.append(buf)
    return parts
