"""Tiny YAML/TOML emitters (stdlib only writes; tomllib/yaml only read or don't exist).

Deliberately minimal: they cover the shapes portover generates (nested dicts,
lists of scalars/dicts, multiline shell strings) — not a general serializer.
"""

from __future__ import annotations

_YAML_BOOLISH = {"true", "false", "yes", "no", "on", "off", "null", "~", ""}


def _yaml_scalar(v) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    s = str(v)
    needs_quote = (
        s.lower() in _YAML_BOOLISH
        or s != s.strip()
        or s[0] in "-?&*!%@`\"'{[|>#,"
        or ": " in s
        or s.endswith(":")
        or "#" in s
        or "\t" in s
        or _numberish(s)
    )
    if not needs_quote:
        return s
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _yaml_key(k) -> str:
    s = str(k)
    if s and " " not in s and ":" not in s and "#" not in s and s[0] not in "-?&*!%@`\"'{[|>,":
        return s  # keys skip the bool/number quoting: idiomatic `on:` stays bare
    return _yaml_scalar(s)


def _numberish(s: str) -> bool:
    try:
        float(s)
        return True
    except ValueError:
        return False


def yaml_dump(obj, indent: int = 0) -> str:
    """Emit a dict as YAML. Multiline strings become literal blocks (|)."""
    pad = "  " * indent
    lines: list[str] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            key = _yaml_key(k)
            if isinstance(v, dict) and v:
                lines.append(f"{pad}{key}:")
                lines.append(yaml_dump(v, indent + 1))
            elif isinstance(v, list) and v:
                lines.append(f"{pad}{key}:")
                for item in v:
                    if isinstance(item, dict):
                        body = yaml_dump(item, indent + 2).splitlines()
                        first = body[0].strip()
                        lines.append(f"{pad}  - {first}")
                        lines.extend(body[1:])
                    else:
                        lines.append(f"{pad}  - {_yaml_scalar(item)}")
            elif isinstance(v, str) and "\n" in v:
                lines.append(f"{pad}{key}: |")
                for ln in v.rstrip("\n").split("\n"):
                    lines.append(f"{pad}  {ln}")
            elif isinstance(v, (dict, list)):  # empty containers
                lines.append(f"{pad}{key}: {{}}" if isinstance(v, dict) else f"{pad}{key}: []")
            else:
                lines.append(f"{pad}{key}: {_yaml_scalar(v)}")
        return "\n".join(lines)
    return pad + _yaml_scalar(obj)


def toml_str(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def toml_value(v) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, list):
        if not v:
            return "[]"
        items = ", ".join(toml_value(i) for i in v)
        if len(items) > 70:
            inner = ",\n    ".join(toml_value(i) for i in v)
            return "[\n    " + inner + ",\n]"
        return "[" + items + "]"
    if isinstance(v, dict):
        return "{ " + ", ".join(f"{k} = {toml_value(x)}" for k, x in v.items()) + " }"
    return toml_str(str(v))
