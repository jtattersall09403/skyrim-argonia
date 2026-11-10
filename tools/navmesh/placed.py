"""Placed-object collision for the navmesh job (inputs.write's `objects`): the built places' references as the
triangles of their meshes' own collision, in world units.

The route infrastructure's persistent references (the WRLD override's `persistentRefs`) are read the same way, their
base's mesh from the intermediate's own STAT/ACTI record or from the plugin that holds it.

Each exterior reference of a `place:` layer in the intermediate (out/build/argonia.json) whose base is a solid type
is looked up in its own plugin (esm.py: MODL and OBND). Its mesh is found as the game finds it (meshes.py: the laid
mod stack's loose files, then BSAs) and its Havok collision read (nif.py: compressed mesh, packed strips, convex
hulls, boxes; the solid layers only). The triangles are scaled, turned by the reference's rotation and moved to its
position. A mesh with no solid collision (a plant, a marker) adds nothing, as in game. A base whose mesh is not on
the VM or not readable falls back to its OBND box (backlog B4's old approximation), counted. Actors, disabled
references and bases with neither mesh nor bounds are left out and counted.

    triangles(data) -> ((n, 3, 3) float64 world units, tally)      the old intermediate's references
    from_shards(refs_dir, data) -> the same                         the new world's refs shards (nw-02 step 8)
"""
from __future__ import annotations

import json
import math
import struct
from pathlib import Path

import numpy as np

from tools.navmesh import esm, nif

ROOT = Path(__file__).resolve().parents[2]
INTERMEDIATE = ROOT / "out" / "build" / "argonia.json"
SOLID = {b"STAT", b"ACTI", b"DOOR", b"CONT", b"FURN", b"MSTT", b"TREE", b"FLOR"}  # items (MISC, BOOK) move: left out


def bases(data: Path, keys: set[str]) -> dict[str, tuple[str, tuple[int, ...] | None]]:
    """FormKey -> (MODL, OBND or None) for the keys found in their own plugin as a solid type, the plugin read where the
    game loads it (meshes.plugin_file: Data, else the laid stack's mod)."""
    out: dict[str, tuple[str, tuple[int, ...] | None]] = {}
    by_plugin: dict[str, set[int]] = {}
    for k in keys:
        local, plugin = k.split(":", 1)
        by_plugin.setdefault(plugin, set()).add(int(local, 16))
    from tools.navmesh.meshes import plugin_file
    for plugin, ids in sorted(by_plugin.items()):
        path = plugin_file(plugin, data)
        if path is None:
            continue
        own = len(esm.masters(path)) << 24
        want = {own | i for i in ids}
        for r in esm.records(path, SOLID, groups=SOLID):
            if r.fid in want:
                modl, ob = "", None
                for sig, p in esm.subrecords(r.data):
                    if sig == b"MODL":
                        modl = p.rstrip(b"\0").decode("cp1252")
                    elif sig == b"OBND" and len(p) == 12:
                        b = struct.unpack("<6h", p)
                        if b[3] > b[0] and b[4] > b[1] and b[5] > b[2]:
                            ob = b
                out[f"{r.fid & 0xFFFFFF:06X}:{plugin}"] = (modl, ob)
    return out


def rotation(rx: float, ry: float, rz: float) -> np.ndarray:
    """A reference's rotation as a matrix on column vectors: Skyrim's angles turn clockwise seen down each axis,
    applied z, then y, then x (the CK's order: the world matrix is Rx(-x) Ry(-y) Rz(-z) on the mesh)."""
    def rot(axis, a):
        c, s = math.cos(a), math.sin(a)
        m = np.eye(3)
        i, j = [(1, 2), (2, 0), (0, 1)][axis]
        m[i, i], m[i, j], m[j, i], m[j, j] = c, -s, s, c
        return m
    return rot(0, -rx) @ rot(1, -ry) @ rot(2, -rz)


def _refs(intermediate: Path, recs: list[dict] | None = None) -> list[dict]:
    """The built places' exterior references plus the route infrastructure's persistent ones (the WRLD override's
    `persistentRefs`: gates, landings, bridges; routes/infra.py), each with the same keys."""
    if recs is None:
        recs = json.loads(intermediate.read_text(encoding="utf-8"))["records"]
    out = [x for r in recs if r.get("layer", "").startswith("place:") and r["type"] == "CELL" and r.get("worldspace")
           for x in r.get("refs", []) if not x.get("actor") and not x.get("disabled")]
    out += [x for r in recs if r["type"] == "WRLD" for x in r.get("persistentRefs", [])
            if not x.get("actor") and not x.get("disabled") and x.get("base") and x.get("pos")]
    return out


def own_models(recs: list[dict]) -> dict[str, str]:
    """FormKey -> MODL of the base records the intermediate itself defines (the infrastructure's gate ACTI, signs,
    new STATs), which no plugin on the VM holds yet."""
    return {r["formKey"]: r["model"] for r in recs if r.get("model") and r.get("formKey") and r["type"] in ("STAT", "ACTI")}


def shard_refs(refs_dir: Path) -> list[dict]:
    """The new world's placed references (nw-02 step 8's per-cell-row shards, `<refs_dir>/*.jsonl`), one JSON object a
    line: {"base": "XXXXXX:Plugin.esm", "pos": [x, y, z], "rot": [rx, ry, rz] radians, "scale": s,
    optional "model": its MODL when the base is new}. Disabled ones are left out."""
    out = []
    for p in sorted(refs_dir.glob("*.jsonl")):
        for ln in p.read_text(encoding="utf-8").splitlines():
            if ln.strip():
                x = json.loads(ln)
                if not x.get("disabled") and x.get("base") and x.get("pos"):
                    out.append(x)
    return out


def from_shards(refs_dir: Path, data: Path, resolver=None) -> tuple[np.ndarray, dict]:
    refs = shard_refs(refs_dir)
    own = {x["base"]: x["model"] for x in refs if x.get("model")}
    return collide(refs, data, own, resolver)


def triangles(data: Path, intermediate: Path = INTERMEDIATE, resolver=None) -> tuple[np.ndarray, dict]:
    recs = json.loads(intermediate.read_text(encoding="utf-8"))["records"]
    return collide(_refs(intermediate, recs), data, own_models(recs), resolver)


def collide(refs: list[dict], data: Path, own: dict[str, str], resolver=None) -> tuple[np.ndarray, dict]:
    """The references' collision triangles in world units: own base models first, then each base's MODL/OBND."""
    from tools.navmesh import meshes
    info = bases(data, {x["base"] for x in refs if x["base"] not in own})
    info.update({k: (m, None) for k, m in own.items()})
    res = resolver or meshes.Resolver(data)
    out: list[np.ndarray] = []
    tally = {"refs": len(refs), "collision": 0, "no_collision": 0, "box_fallback": 0, "no_base": 0, "triangles": 0}
    for x in sorted(refs, key=lambda r: r.get("formKey", "")):
        modl, ob = info.get(x["base"], ("", None))
        c = res.collision(modl) if modl else None
        if c is not None and c.tris is not None:
            local = c.tris
            tally["collision" if len(local) else "no_collision"] += 1
        elif ob is not None:
            local = nif._box_tris(np.array(ob[:3], float), np.array(ob[3:], float))
            tally["box_fallback"] += 1
        else:
            tally["no_base"] += 1
            continue
        if not len(local):
            continue
        m = rotation(*x["rot"]) * float(x.get("scale") or 1.0)
        out.append(local.reshape(-1, 3) @ m.T + np.array(x["pos"], float))
    tris = np.concatenate(out).reshape(-1, 3, 3) if out else np.zeros((0, 3, 3))
    tally["triangles"] = len(tris)
    return tris, tally
