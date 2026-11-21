"""Where the camera may stand: the order a view retries in when a capture fails, and a person's eye standing on the
walkable ground or a deck, never inside a piece. Pure functions (tools/tests/test_places_look.py)."""
from __future__ import annotations

import math

import numpy as np

from tools.places.look import capture, geom

SIDES8 = ["n", "ne", "e", "se", "s", "sw", "w", "nw"]
TALL = 1.6        # a subject this many times taller than wide is framed whole, and its base in a second view
TALL_MIN = 600.0  # and at least this tall


def by_turn(side: str) -> list[str]:
    """The eight sides, nearest first to the one asked for."""
    i = SIDES8.index(side)
    return [SIDES8[(i + k) % 8] for k in (0, 1, -1, 2, -2, 3, -3, 4)]


def candidates(side: str, height: str, canopy_cut: bool = False, n: int = 12,
               distance: float = 1.0) -> list[tuple[str, str, float, bool]]:
    """The tries of one view, in order: (side, height, distance scale, canopy cut). The one asked for first, then the
    other sides, then further away, then higher, then with the canopy cut away. `distance` scales every try's
    distance (`at --distance 2` stands twice as far back, 0.5 half as far)."""
    out: list[tuple[str, str, float, bool]] = []
    sides = by_turn(side)

    def add(t):
        t = (t[0], t[1], round(t[2] * distance, 3), t[3])
        if t not in out:
            out.append(t)
    add((side, height, 1.0, canopy_cut))
    for s in sides[1:5]:
        add((s, height, 1.0, canopy_cut))
    add((side, height, 1.6, canopy_cut))
    for hh in ("oblique", "high"):
        if hh != height:
            add((side, hh, 1.0, canopy_cut))
    add((side, height, 1.0, True))
    add((side, "high", 1.3, True))
    for s in sides[1:4]:
        add((s, "high", 1.3, True))
    return out[:n]


def is_tall(lo, hi) -> bool:
    lo, hi = np.asarray(lo, float), np.asarray(hi, float)
    tall = float(hi[2] - lo[2])
    return tall >= TALL_MIN and tall > TALL * float(max(hi[0] - lo[0], hi[1] - lo[1]))


def base_box(lo, hi) -> tuple[list, list]:
    """The lower part of a tall subject: as high as it is wide (at least a person's height and a half)."""
    lo, hi = np.asarray(lo, float), np.asarray(hi, float)
    wide = float(max(hi[0] - lo[0], hi[1] - lo[1]))
    return lo.tolist(), [float(hi[0]), float(hi[1]), float(lo[2] + max(wide, 1.5 * geom.PERSON))]


def stand(target, away, want: float, floor, blocked, scales=(1.0, 0.8, 1.25, 0.6, 1.6, 0.45, 2.0),
          turns=(0, 20, -20, 40, -40, 65, -65)) -> dict | None:
    """A person's eye for looking at target from the direction `away` (xy) about `want` units off: the first spot,
    nearest the asked distance and side, where floor(x, y) gives a surface a person stands on and blocked(eye) is
    None. Returns {pos, scale, turn} or None."""
    t = np.asarray(target[:2], float)
    u = np.asarray(away[:2], float)
    u = u / max(float(np.linalg.norm(u)), 1e-9)
    for s in scales:
        for a in turns:
            r = math.radians(a)
            v = np.array([u[0] * math.cos(r) - u[1] * math.sin(r), u[0] * math.sin(r) + u[1] * math.cos(r)])
            x, y = t + v * want * s
            z = floor(float(x), float(y))
            if z is None:
                continue
            eye = [float(x), float(y), float(z) + geom.EYE]
            if blocked(eye) or blocked([eye[0], eye[1], float(z) + 40.0]):
                continue
            return {"pos": [round(v_, 2) for v_ in eye], "scale": s, "turn": a, "floor": round(float(z), 1)}
    return None


def blocker(pieces: list[dict], ground) -> callable:
    """blocked(eye): why a camera there cannot see (capture.camera_inside), over the pieces near it."""
    boxes = [(p, *geom.aabb(p)) for p in pieces if p.get("model")]

    def blocked(eye, crowns_cut=None):
        near = [p for p, lo, hi in boxes if lo[0] - 8 <= eye[0] <= hi[0] + 8 and lo[1] - 8 <= eye[1] <= hi[1] + 8
                and lo[2] - 8 <= eye[2] <= hi[2] + 8]
        g = ground.height(eye[0], eye[1]) if ground is not None else None
        return capture.camera_inside(eye, near, g, crowns_cut=crowns_cut)
    return blocked


STAND_EYE = 120.0   # `at --stand x,y`: the eye this far over the surface under the point


def _posed_near(pieces: list[dict], x: float, y: float):
    from tools.places import shape
    for p in pieces:
        if not p.get("model") or not geom.solid(p):
            continue
        lo, hi = geom.aabb(p)
        if lo[0] - shape.CELL <= x <= hi[0] + shape.CELL and lo[1] - shape.CELL <= y <= hi[1] + shape.CELL:
            yield p, shape.posed(p)


def stand_surface(pieces: list[dict], ground, x: float, y: float) -> tuple[float | None, str | None]:
    """The surface a person stands on at (x, y): the lowest walked surface of a piece's mesh (shape.py: its walk or
    lowest walk) over the ground there (a stilt deck, not the roof over it), else the ground. (height, piece id)."""
    g = ground.height(x, y) if ground is not None else None
    best = None
    for p, S in _posed_near(pieces, x, y):
        for f in ("walk", "walk_low"):
            w = S.at(x, y, f)
            if w is not None and (g is None or w >= g - 8.0) and (best is None or w < best[0]):
                best = (w, p["id"])
    return best if best is not None else (g, None)


def inside_mesh(pieces: list[dict], pt) -> str | None:
    """The piece whose mesh holds the point (between its underside and its top there, not standing over a walked
    surface of it: a hut's own floor under its roof is room to stand in), else None."""
    x, y, z = (float(v) for v in pt[:3])
    for p, S in _posed_near(pieces, x, y):
        u, t = S.at(x, y, "under"), S.at(x, y, "top")
        if u is None or t is None or not (u + 4.0 < z < t - 4.0):
            continue
        floors = [w for f in ("walk", "walk_low") if (w := S.at(x, y, f)) is not None and w <= z]
        if any(z - w <= STAND_EYE + 2 * geom.PERSON for w in floors):
            continue
        return f"{p.get('edid') or p['id']} ({p['id']})"
    return None


def stand_camera(pieces: list[dict], ground, point, lo, hi, w: int, h: int, fov: float = 60.0) -> dict:
    """`at <subject> --stand x,y[,z]`: a camera at the eye (STAND_EYE) over the surface under (x, y) (stand_surface),
    or at z when given, looking at the subject box's middle. Refused (ValueError) inside a piece's mesh."""
    x, y = float(point[0]), float(point[1])
    if len(point) > 2:
        eye, on = [x, y, float(point[2])], "asked"
    else:
        z, on = stand_surface(pieces, ground, x, y)
        if z is None:
            raise ValueError(f"--stand {x:.0f},{y:.0f}: no ground or deck under the point")
        eye, on = [x, y, float(z) + STAND_EYE], on or "ground"
    hit = inside_mesh(pieces, eye)
    if hit:
        raise ValueError(f"--stand {','.join(f'{v:.0f}' for v in eye)} is inside the mesh of {hit}: stand elsewhere")
    tgt = (np.asarray(lo, float) + np.asarray(hi, float)) / 2
    d = float(np.linalg.norm(tgt - np.asarray(eye)))
    r = float(np.linalg.norm(np.asarray(hi, float) - np.asarray(lo, float))) / 2
    return {"pos": [round(v, 2) for v in eye], "target": [round(float(v), 2) for v in tgt], "up": [0, 0, 1],
            "fov": fov, "w": w, "h": h, "near": 8, "far": round(d + 3 * r + 2000), "stood": {"on": on}}
