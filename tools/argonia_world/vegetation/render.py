"""The placements as terrain/render.py's "placements" layer (lane 1.15-r4-trees: the registry named this module, which
did not exist, so no L3 render ever drew a placement). Points coloured by kind: a tree by its family (lists.FAMILY,
so the classes' different forests read apart), anything else by its role (layer.COLOURS).

The shards are ARGONIA_VEG_OUT (default out/vegetation)."""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np

from tools.argonia_world import skyrim_units as su
from tools.argonia_world.vegetation import build, layer, lists

FAMILY_RGB = {"mangrove": (40, 140, 140), "palm": (230, 220, 60), "cypress": (20, 90, 30), "willow": (130, 220, 110),
              "jungle": (0, 160, 60), "hist": (160, 40, 160), "dead": (150, 120, 100), "broadleaf": (240, 140, 40)}


def render_layer(w) -> np.ndarray | None:
    from tools.argonia_world.terrain.cellwater import Q
    out = Path(os.environ.get("ARGONIA_VEG_OUT") or layer.ROOT / "out" / "vegetation")
    if not out.exists():
        return None
    world = w.world
    if world is None:
        from tools.argonia_world import db
        world = db.open()
    rgb_of = {}
    for f in world.query("SELECT form_key, edid, model, role_id FROM object_form"):
        fam = lists.family(f) if f["role_id"] in lists.TREE_ROLES else None
        rgb_of[f["form_key"]] = FAMILY_RGB.get(fam[0]) if fam else layer.COLOURS.get(f["role_id"], (255, 0, 0))
    h, wd = w.ground.shape
    ov = np.zeros((h, wd, 4), np.uint8)
    for c in build.read_cells(out):
        if not (w.x0 <= c["x"] <= w.x1 and w.y0 <= c["y"] <= w.y1):
            continue
        for r in c["refs"]:
            col = int((r[2] / su.CELL_UNITS - w.x0) * Q)
            row = int((w.y1 + 1 - r[3] / su.CELL_UNITS) * Q)
            ov[max(row - 1, 0):row + 1, max(col - 1, 0):col + 1] = (*(rgb_of.get(c["bases"][r[1]]) or (255, 0, 0)), 255)
    return ov
