"""The placements as a render layer for terrain/render.py's L3 renders (1.15 §e.3): points coloured by form class.

    render_layer(window, out=out/vegetation, world=None) -> {"x": game units, "y": game units, "rgb": (n, 3) uint8,
                                                            "role": [str], "legend": {role: (r, g, b)}}
`window` is (cx0, cy0, cx1, cy1) in province cells, inclusive; only the shards of its rows are read.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

from tools.argonia_world.vegetation import build

ROOT = Path(__file__).resolve().parents[3]
COLOURS = {"canopy": (34, 110, 40), "emergent": (10, 60, 20), "gallery": (90, 160, 70), "mangrove": (40, 90, 90),
           "palm": (170, 190, 60), "shrub": (120, 200, 90), "aquatic": (60, 160, 220), "mushroom": (200, 60, 200),
           "deadwood": (120, 85, 50), "rock": (150, 150, 150), "cliff-tree": (70, 120, 60)}


def render_layer(window, out: Path | None = None, world=None) -> dict:
    from tools.argonia_world import db
    out = Path(out or ROOT / "out" / "vegetation")
    w = world if world is not None else db.open()
    role = {r["form_key"]: r["role_id"] for r in w.query("SELECT form_key, role_id FROM object_form")}
    cx0, cy0, cx1, cy1 = window
    xs, ys, roles = [], [], []
    for c in build.read_cells(out):
        if not (cx0 <= c["x"] <= cx1 and cy0 <= c["y"] <= cy1):
            continue
        for r in c["refs"]:
            xs.append(r[2])
            ys.append(r[3])
            roles.append(role.get(c["bases"][r[1]], "shrub"))
    rgb = np.array([COLOURS.get(r, (255, 0, 0)) for r in roles], np.uint8).reshape(-1, 3)
    return {"x": np.asarray(xs, float), "y": np.asarray(ys, float), "rgb": rgb, "role": roles, "legend": COLOURS}
