"""The quest form's schema check: schema.json applied by a small JSON Schema reader (stdlib only).

It reads the keywords schema.json uses and no others: type, properties, required, additionalProperties (false),
enum, const, items, minItems, minLength, minimum, maximum, oneOf and local $ref. A schema keyword it does not know
is an error, so schema.json cannot grow a keyword this reader silently skips.
"""
from __future__ import annotations

import json
from pathlib import Path

SCHEMA = json.loads((Path(__file__).with_name("schema.json")).read_text(encoding="utf-8"))
KNOWN = {"$schema", "$id", "title", "$defs", "type", "properties", "required", "additionalProperties", "enum",
         "const", "items", "minItems", "minLength", "minimum", "maximum", "oneOf", "$ref"}
# the field that names which shape of a oneOf a value means: its errors are reported against that shape
DISCRIMINATORS = ("is", "do", "kind", "by")


def _type_ok(v, t: str) -> bool:
    return {
        "object": isinstance(v, dict),
        "array": isinstance(v, list),
        "string": isinstance(v, str),
        "boolean": isinstance(v, bool),
        "integer": isinstance(v, int) and not isinstance(v, bool),
        "number": isinstance(v, (int, float)) and not isinstance(v, bool),
        "null": v is None,
    }[t]


def _resolve(s: dict) -> dict:
    while "$ref" in s:
        ref = s["$ref"]
        if not ref.startswith("#/"):
            raise ValueError(f"schema: only local $ref is read, not {ref}")
        node = SCHEMA
        for part in ref[2:].split("/"):
            node = node[part]
        s = node
    return s


def _matches_discriminator(v, s: dict) -> bool:
    s = _resolve(s)
    props = s.get("properties", {})
    for k in DISCRIMINATORS:
        if isinstance(v, dict) and k in v and k in props:
            p = props[k]
            return v[k] == p.get("const") or v[k] in p.get("enum", [])
    return False


def errors(v, s: dict | None = None, path: str = "$") -> list[str]:
    """Every way `v` breaks the schema (schema.json when `s` is None), each as 'path: what'."""
    s = _resolve(SCHEMA if s is None else s)
    bad = set(s) - KNOWN
    if bad:
        raise ValueError(f"schema at {path}: keyword(s) {sorted(bad)} are not read by this checker")
    if "const" in s and v != s["const"]:
        return [f"{path}: must be {s['const']!r}"]
    if "enum" in s and v not in s["enum"]:
        return [f"{path}: {v!r} is not one of {s['enum']}"]
    if "type" in s:
        types = s["type"] if isinstance(s["type"], list) else [s["type"]]
        if not any(_type_ok(v, t) for t in types):
            return [f"{path}: must be {' or '.join(types)}"]
    out: list[str] = []
    if "oneOf" in s:
        branches = s["oneOf"]
        passing = [b for b in branches if not errors(v, b, path)]
        if len(passing) == 1:
            return []
        if len(passing) > 1:
            return [f"{path}: matches more than one shape"]
        named = [b for b in branches if _matches_discriminator(v, b)]
        if len(named) == 1:
            return errors(v, named[0], path)
        what = v.get(next((k for k in DISCRIMINATORS if isinstance(v, dict) and k in v), ""), None) \
            if isinstance(v, dict) else None
        return [f"{path}: {('unknown word ' + repr(what)) if what is not None else 'not one of the allowed shapes'}"]
    if isinstance(v, str) and len(v) < s.get("minLength", 0):
        out.append(f"{path}: must not be empty")
    if _type_ok(v, "number"):
        if "minimum" in s and v < s["minimum"]:
            out.append(f"{path}: below {s['minimum']}")
        if "maximum" in s and v > s["maximum"]:
            out.append(f"{path}: above {s['maximum']}")
    if isinstance(v, list):
        if len(v) < s.get("minItems", 0):
            out.append(f"{path}: needs at least {s['minItems']} item(s)")
        if "items" in s:
            for i, e in enumerate(v):
                out += errors(e, s["items"], f"{path}[{i}]")
    if isinstance(v, dict):
        props = s.get("properties", {})
        for k in s.get("required", []):
            if k not in v:
                out.append(f"{path}: missing {k!r}")
        if s.get("additionalProperties") is False:
            for k in v:
                if k not in props:
                    out.append(f"{path}: {k!r} is not a field of the form")
        for k, sub in props.items():
            if k in v:
                out += errors(v[k], sub, f"{path}.{k}")
    return out
