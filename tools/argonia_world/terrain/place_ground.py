"""The built places' ground edits (0.4 §d), as a layer on the ground: the world db's `build_ground` rows.

Each row is a bowl: the ground carved down to `floor_m` within `flat_radius_m` of its province point, its side rising
`side_rise` metres per metre beyond that until it meets the ground. It is a ceiling only (h = min(h, bowl)), so it
never raises anything. `Sources.heights` applies it to the province ground before the water's regrade
(water_regrade.py), so the water plan (which stands on `Sources.load`), the LAND, its normals,
`build.game_heights_m` and the navmesh all carry it. It never edits the frozen arrays.
"""
from __future__ import annotations

import hashlib
import math

import numpy as np

from tools.argonia_world import skyrim_units as su

TABLE = "build_ground"
REACH_M = 20.0  # no bowl's side reaches further than this beyond its floor


class Edits:
    def __init__(self, bowls: list[tuple[float, float, float, float, float]], pad: int):
        """Bowls as (column, row, floor m, flat radius m, side rise) in province samples; `pad`: the grid's pad."""
        self.bowls, self.pad = bowls, pad

    def __len__(self) -> int:
        return len(self.bowls)

    @classmethod
    def load(cls, pad: int, world=None) -> "Edits | None":
        from tools.argonia_world import db
        w = world if world is not None else db.open()
        try:
            rows = w.query(f'SELECT x_m, y_m, floor_m, flat_radius_m, side_rise FROM "{TABLE}" ORDER BY id')
        except Exception:  # an older schema without the table
            return None
        if not rows:
            return None
        s = su.PROVINCE_SAMPLE_M
        return cls([(r[0] / s, r[1] / s, r[2], r[3], r[4]) for r in rows], pad)

    def apply(self, out: np.ndarray, r0: int, c0: int) -> None:
        """Lower `out` (a window whose first grid row and column are r0, c0) to every bowl inside it."""
        s = su.PROVINCE_SAMPLE_M
        for col, row, floor, flat, rise in self.bowls:
            reach = math.ceil((flat + REACH_M) / s)
            gc, gr = col + self.pad, row + self.pad
            i0, i1 = max(r0, math.floor(gr) - reach), min(r0 + out.shape[0], math.ceil(gr) + reach + 1)
            j0, j1 = max(c0, math.floor(gc) - reach), min(c0 + out.shape[1], math.ceil(gc) + reach + 1)
            if i0 >= i1 or j0 >= j1:
                continue
            rr, cc = np.mgrid[i0:i1, j0:j1]
            d = np.hypot(rr - gr, cc - gc) * s
            bowl = floor + np.maximum(0.0, d - flat) * rise
            win = out[i0 - r0:i1 - r0, j0 - c0:j1 - c0]
            np.minimum(win, bowl, out=win)


def stamp(world=None) -> str:
    """The table's content hash, for the terrain's rebuild stamp."""
    from tools.argonia_world import db
    w = world if world is not None else db.open()
    try:
        rows = w.query(f'SELECT id, x_m, y_m, floor_m, flat_radius_m, side_rise FROM "{TABLE}" ORDER BY id')
    except Exception:
        return "none"
    return hashlib.sha256(repr([tuple(r) for r in rows]).encode()).hexdigest()
