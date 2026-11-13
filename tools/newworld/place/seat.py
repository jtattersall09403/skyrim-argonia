"""Seat a placed thing by its kind's rule from its own mesh (tools/newworld/place/audit.py): the edits stage's `seat`
row over one base. The placement already seats every thing by that rule (place.py step 7), so a `seat` row changes a
thing only when the ground under it changed since; it keeps the thing's identity, form id, x, y, rotation and scale.

    python -m tools.newworld.place.seat audit [--json OUT]   the seating audit of the placed refs (audit.py refs)
"""
from __future__ import annotations

import argparse
import sys

import numpy as np

from tools.newworld.place import audit as A
from tools.newworld.place import place as P


def rot_matrix(rx: float, ry: float, rz: float) -> np.ndarray:
    """Kept for dressing/hang_points.py, its one reader: the transpose of Skyrim's reference rotation
    (tools.navmesh.placed.rotation, which the seating uses); a turn about z goes the other way."""
    cx, sx, cy, sy, cz, sz = np.cos(rx), np.sin(rx), np.cos(ry), np.sin(ry), np.cos(rz), np.sin(rz)
    return (np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]]) @ np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
            @ np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]]))


class Seater:
    """seat(o, embed_m) -> the thing's z seated by its kind's rule, or None when it stands as it is."""

    def __init__(self, world=None, resolver=None):
        self.W, self.prof = world, A.Profiles(resolver)

    def ground(self, xs, ys):
        if self.W is None:
            self.W = P.World()
        t1, t2 = self.W.tri_grounds(np.asarray(xs, float), np.asarray(ys, float))
        return np.minimum(t1, t2)

    def seat(self, o: dict, embed_m: float = 0.1) -> float | None:
        p = self.prof(o["model"])
        if p is None:
            return None
        got = A.seat(p, o.get("cls") or "", o["pos"], o["rot"], o["scale"], self.ground)
        if got is None:
            return None
        z = round(float(got[0]), 1)
        return z if abs(z - float(o["pos"][2])) >= 0.1 else None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=["audit"])
    ap.add_argument("--json")
    a = ap.parse_args(argv)
    return A.main(["refs"] + (["--json", a.json] if a.json else []))


if __name__ == "__main__":
    sys.exit(main())
