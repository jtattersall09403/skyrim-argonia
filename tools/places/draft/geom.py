"""Footprints, frames and transforms used across the draft."""
from __future__ import annotations

import math

from tools.places.seat import foot_radius, model_bounds

LEVELLED = {"LVLN", "LVLI", "LVSP", "LeveledNpc", "LeveledItem", "LeveledSpell"}
POINT_KINDS = {"marker", "actor", "light", "clutter", "groundcover"}


def solid(base: dict) -> bool:
    """A thing with a body one stands on or walks round (effects, fog and markers have bounds but no body)."""
    m = str(base.get("model") or "").lower()
    return bool(m) and not m.startswith(("effects/", "fx", "markers/")) and "/fx" not in m


def bounds(ref: dict, bases: dict) -> tuple[list[float], list[float]] | None:
    base = bases.get(ref.get("base")) or {}
    b = model_bounds(base) if solid(base) else None
    if not b:
        return None
    s = float(ref.get("scale") or 1.0)
    return [v * s for v in b[0]], [v * s for v in b[1]]


def foot(ref: dict, bases: dict, min_half: float = 24.0) -> list[float] | None:
    """A ref's true footprint [x0, y0, x1, y1] in its own frame (scaled), or None for a small thing."""
    b = bounds(ref, bases)
    if not b:
        return None
    hx, hy = (b[1][0] - b[0][0]) / 2, (b[1][1] - b[0][1]) / 2
    if max(hx, hy) < min_half or ref.get("kind") in POINT_KINDS:
        return None
    return [round(b[0][0], 1), round(b[0][1], 1), round(b[1][0], 1), round(b[1][1], 1)]


def radius(ref: dict, bases: dict) -> float:
    f = foot(ref, bases, 0.0)
    return foot_radius(f) if f else 32.0


def reach(ref: dict, bases: dict) -> float:
    """How far from its origin a ref's footprint reaches."""
    return radius(ref, bases)


def bottom(ref: dict, bases: dict) -> float:
    b = bounds(ref, bases)
    return ref["pos"][2] + (b[0][2] if b else 0.0)


def top(ref: dict, bases: dict) -> float:
    b = bounds(ref, bases)
    return ref["pos"][2] + (b[1][2] if b else 0.0)


def contains_xy(sup: dict, bases: dict, x: float, y: float, pad: float = 0.0) -> bool:
    b = bounds(sup, bases)
    if not b:
        return False
    rz = sup.get("rot", [0, 0, 0])[2]
    dx, dy = x - sup["pos"][0], y - sup["pos"][1]
    c, s = math.cos(rz), math.sin(rz)
    u, v = dx * c - dy * s, dx * s + dy * c   # world -> local (inverse of the clockwise yaw)
    return b[0][0] - pad <= u <= b[1][0] + pad and b[0][1] - pad <= v <= b[1][1] + pad


class Xf:
    """A 2D rigid transform of the source frame onto ours: rotate by `rot` (clockwise yaw, radians) about the
    source pivot, then move the pivot to `to`."""

    def __init__(self, pivot, to, rot: float):
        self.pivot, self.to, self.rot = tuple(pivot), tuple(to), rot
        self.c, self.s = math.cos(rot), math.sin(rot)

    def pt(self, x: float, y: float) -> tuple[float, float]:
        dx, dy = x - self.pivot[0], y - self.pivot[1]
        return (self.to[0] + dx * self.c + dy * self.s, self.to[1] - dx * self.s + dy * self.c)

    def yaw(self, rz: float) -> float:
        return (rz + self.rot) % (2 * math.pi)

    def then(self, dx: float, dy: float, drot: float, about) -> "Xf":
        """This transform followed by a turn of drot about `about` (in our frame) and a shift (dx, dy)."""
        p2 = self.pt(*self.pivot)
        a = (about[0], about[1])
        c, s = math.cos(drot), math.sin(drot)
        ox, oy = p2[0] - a[0], p2[1] - a[1]
        p3 = (a[0] + ox * c + oy * s + dx, a[1] - ox * s + oy * c + dy)
        return Xf(self.pivot, p3, self.rot + drot)

    def as_dict(self) -> dict:
        return {"pivot": [round(v, 1) for v in self.pivot], "to": [round(v, 1) for v in self.to],
                "rot": round(self.rot, 5)}


def dist(a, b) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def mesh_bounds(base: dict) -> list | None:
    return model_bounds(base)


def plane(base: dict, scale: float = 1.0) -> dict | None:
    """A door-like piece's plane in its own frame: the thin horizontal axis (0 = x, 1 = y), the centre and the width."""
    b = mesh_bounds(base)
    if not b:
        return None
    ex, ey = (b[1][0] - b[0][0]) * scale, (b[1][1] - b[0][1]) * scale
    return {"axis": 0 if ex < ey else 1, "centre": [(b[0][0] + b[1][0]) / 2 * scale, (b[0][1] + b[1][1]) / 2 * scale],
            "width": max(ex, ey)}


def turn(v, rz: float) -> tuple[float, float]:
    """A local offset turned by a clockwise yaw into the world."""
    c, s = math.cos(rz), math.sin(rz)
    return (v[0] * c + v[1] * s, -v[0] * s + v[1] * c)


def align(old: dict, new: dict, turn_deg: float | None) -> dict | None:
    """How to set a replacement so its plane lies where the original's did: the turn (the agent's when it lines the
    planes up, else the nearest that does) and the shift of the origin, in the original's frame."""
    po, pn = plane(old), plane(new)
    if not po or not pn:
        return None
    t = float(turn_deg or 0.0)
    if (pn["axis"] + round(t / 90)) % 2 != po["axis"]:
        t = (t + 90.0) % 360.0
    rn = turn(pn["centre"], math.radians(t))
    return {"turn_deg": t, "shift_local": [round(po["centre"][0] - rn[0], 1), round(po["centre"][1] - rn[1], 1)],
            "width_ratio": round(pn["width"] / po["width"], 2) if po["width"] else None}
