"""Placed-object collision for the navmesh job (inputs.write's `objects`): the built places' references as boxes.

Each exterior reference of a `place:` layer in the intermediate (out/build/argonia.json) whose base record carries
object bounds (OBND, read from the base's own plugin with esm.py) becomes the box of those bounds, scaled, turned by
its z rotation and moved to its position, as its eight corners. ArgoniaNav rasterises each box solid (Recast's
filled-volume box): its top is walkable as any span and its sides block. This is the bounds of the record, not the mesh's collision: the masters'
meshes are not on the build VM (2.W4 §b), so a hut's doorway or a dock's underside is solid here. Actors, items
(MISC, BOOK), markers and records without bounds (our own STATs: no OBND without the mesh) are left out and
counted.
"""
from __future__ import annotations

import json
import math
import struct
from pathlib import Path

import numpy as np

from tools.navmesh import esm

ROOT = Path(__file__).resolve().parents[2]
INTERMEDIATE = ROOT / "out" / "build" / "argonia.json"
SOLID = {b"STAT", b"ACTI", b"DOOR", b"CONT", b"FURN", b"MSTT", b"TREE", b"FLOR"}


def _bounds(data: Path, keys: set[str]) -> dict[str, tuple[int, ...]]:
    """FormKey -> OBND (x1, y1, z1, x2, y2, z2) for the keys whose base has bounds, from each key's own plugin."""
    out: dict[str, tuple[int, ...]] = {}
    by_plugin: dict[str, set[int]] = {}
    for k in keys:
        local, plugin = k.split(":", 1)
        by_plugin.setdefault(plugin, set()).add(int(local, 16))
    for plugin, ids in sorted(by_plugin.items()):
        path = data / plugin
        if not path.exists():
            continue
        own = len(esm.masters(path)) << 24
        want = {own | i for i in ids}
        for r in esm.records(path, SOLID, groups=SOLID):
            if r.fid in want:
                for sig, p in esm.subrecords(r.data):
                    if sig == b"OBND" and len(p) == 12:
                        b = struct.unpack("<6h", p)
                        if b[3] > b[0] and b[4] > b[1] and b[5] > b[2]:
                            out[f"{r.fid & 0xFFFFFF:06X}:{plugin}"] = b
                        break
    return out


def boxes(data: Path, intermediate: Path = INTERMEDIATE) -> tuple[np.ndarray, dict]:
    """(k, 8, 3) world-unit corners of every placed box (corner i: bit 0 x max, bit 1 y max, bit 2 z max, before
    the turn), and the tally of what was left out and why."""
    recs = json.loads(intermediate.read_text(encoding="utf-8"))["records"]
    refs = [x for r in recs if r.get("layer", "").startswith("place:") and r["type"] == "CELL" and r.get("worldspace")
            for x in r.get("refs", []) if not x.get("actor") and not x.get("disabled")]
    bounds = _bounds(data, {x["base"] for x in refs})
    out, tally = [], {"refs": len(refs), "boxes": 0, "no_bounds": 0}
    corners = np.array([[(i >> 0) & 1, (i >> 1) & 1, (i >> 2) & 1] for i in range(8)], dtype=np.float64)
    for x in refs:
        b = bounds.get(x["base"])
        if b is None:
            tally["no_bounds"] += 1
            continue
        lo, hi = np.array(b[:3], np.float64), np.array(b[3:], np.float64)
        c = (lo + corners * (hi - lo)) * float(x.get("scale") or 1.0)
        rz = x["rot"][2]  # Skyrim's z rotation: clockwise from above
        cz, sz = math.cos(rz), math.sin(rz)
        xy = np.stack([c[:, 0] * cz + c[:, 1] * sz, -c[:, 0] * sz + c[:, 1] * cz], axis=1)
        out.append(np.column_stack([xy + np.array(x["pos"][:2]), c[:, 2] + x["pos"][2]]))
        tally["boxes"] += 1
    return (np.array(out, np.float64) if out else np.zeros((0, 8, 3))), tally
