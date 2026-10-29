"""Load and validate the world's authored record families (ported from the old
repo's packages/world-schema/world_schema.py, decision 0104).

``world/schemas/families.json`` is the registry; ``world/schemas/*.schema.json``
holds one JSON Schema per family, keyed by ``$id`` so a schema can ``$ref``
another. Validation uses ``jsonschema`` (the only third-party import; both the
``referencing`` registry and the older ``RefResolver`` are supported).
"""
from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

try:  # jsonschema >= 4.18
    from referencing import Registry, Resource
except ImportError:  # older jsonschema
    Registry = Resource = None
    from jsonschema import RefResolver

_STATE: dict = {"dir": None, "by_file": None, "registry": None, "store": None, "families": None}


def configure(schema_dir: Path) -> None:
    """Point the loader at ``world/schemas`` and read every schema once."""
    schema_dir = Path(schema_dir)
    by_file, store = {}, {}
    registry = Registry() if Registry else None
    for path in sorted(schema_dir.glob("*.schema.json")):
        schema = json.loads(path.read_text(encoding="utf-8"))
        by_file[path.name] = schema
        store[schema["$id"]] = schema
        if registry is not None:
            registry = registry.with_resource(schema["$id"], Resource.from_contents(schema))
    fam = json.loads((schema_dir / "families.json").read_text(encoding="utf-8"))["families"]
    _STATE.update(dir=schema_dir, by_file=by_file, registry=registry, store=store, families=fam)


def families() -> dict[str, dict]:
    return _STATE["families"]


def validator(family: str) -> Draft202012Validator:
    schema = _STATE["by_file"][families()[family]["schema"]]
    if _STATE["registry"] is not None:
        return Draft202012Validator(schema, registry=_STATE["registry"])
    schema = _absolute(schema)
    store = {k: _absolute(v) for k, v in _STATE["store"].items()}
    store = {v["$id"]: v for v in store.values()}
    resolver = RefResolver.from_schema(schema, store=store)
    return Draft202012Validator(schema, resolver=resolver)


_BASE = "https://argonia.invalid/"


def _absolute(node):
    """Older jsonschema resolves a relative `$id` against itself; give every id and
    cross-schema `$ref` an absolute base so `world-schema/socket.v1` resolves."""
    if isinstance(node, dict):
        out = {}
        for k, v in node.items():
            if k == "$id" and isinstance(v, str) and not v.startswith("http"):
                v = _BASE + v
            elif k == "$ref" and isinstance(v, str) and not v.startswith(("#", "http")):
                v = _BASE + v
            out[k] = _absolute(v)
        return out
    if isinstance(node, list):
        return [_absolute(v) for v in node]
    return node


def validate(family: str, doc: object) -> list[str]:
    """Every schema error of ``doc`` as ``<json path>: <message>``."""
    return [f"{'/'.join(str(p) for p in e.absolute_path) or '<root>'}: {e.message}"
            for e in sorted(validator(family).iter_errors(doc), key=lambda e: [str(p) for p in e.absolute_path])]


def load_family(family: str, root: Path) -> list[tuple[Path, dict]]:
    """(path, document) for every file of a family under ``root``."""
    out = []
    for pattern in families()[family].get("files") or []:
        for path in sorted(Path(root).glob(pattern)):
            out.append((path, json.loads(path.read_text(encoding="utf-8"))))
    return out
