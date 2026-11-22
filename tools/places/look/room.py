"""A room as the look tool sees it: which space a name means, the room's floor (the walkable mesh its source cell
was built with, kept to the room's cut), where a camera may stand inside it, and the points the void test looks out
from. Pure numbers (tested on small fixtures); scene.py composes the room's pieces, verbs.py draws and asks the page.

The room's floor stands in for the ground of the exterior: a piece's height over the ground is its height over the
floor under it, a door's ground is the floor before it."""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

CEILING = 330.0      # a room seen from above: what rises more than this over its floor is cut away (the ceiling)


def space_id(spaces: dict, name: str) -> str:
    """The space a name means: its id, the name its door shows (space.json `name`), any case; KeyError with the
    rooms there are."""
    n = name.strip().lower()
    if n in ("exterior", "outside"):
        return "exterior"
    for sid, sp in spaces.items():
        if sid.lower() == n or str(((sp or {}).get("space") or {}).get("name") or "").lower() == n:
            return sid
    near = [sid for sid in spaces if n in sid.lower() or n in str(((spaces[sid] or {}).get("space") or {}).get("name") or "").lower()]
    if len(near) == 1:
        return near[0]
    raise KeyError(f"no room named {name!r}; rooms: "
                   + ", ".join(f"{sid} ({(sp.get('space') or {}).get('name')})" for sid, sp in sorted(spaces.items())
                               if sid != "exterior"))


class Floor:
    """A room's floor as a ground: height(x, y) is the walkable mesh under the point (the highest when floors stack),
    None off it; water() is None (a room has no water level the look tool reads)."""

    def __init__(self, verts, tris):
        self.V = np.asarray(verts, float).reshape(-1, 3)
        self.T = np.asarray(tris, int).reshape(-1, 3)
        a, b, c = (self.V[self.T[:, k]] for k in range(3)) if len(self.T) else (np.zeros((0, 3)),) * 3
        self.a, self.b, self.c = a, b, c
        self.lo = np.minimum(np.minimum(a, b), c)
        self.hi = np.maximum(np.maximum(a, b), c)
        self.floor = float(np.median(self.V[self.T].reshape(-1, 3)[:, 2])) if len(self.T) else 0.0
        self.zmin = float(self.V[self.T].reshape(-1, 3)[:, 2].min()) if len(self.T) else 0.0

    def height(self, x: float, y: float):
        if not len(self.T):
            return None
        m = np.nonzero((self.lo[:, 0] <= x) & (x <= self.hi[:, 0]) & (self.lo[:, 1] <= y) & (y <= self.hi[:, 1]))[0]
        best = None
        for i in m:
            h = _height_in(self.a[i], self.b[i], self.c[i], x, y)
            if h is not None and (best is None or h > best):
                best = h
        return best

    def height_below(self, x: float, y: float, z: float, tol: float = 64.0):
        """Where floors stack (a ship's hold under its deck): the floor a thing at height z stands over, the highest
        surface no more than `tol` over z; a thing under the room's lowest walked floor is measured against the lowest
        surface there; one where only a deck above it is walked (the walkable mesh cut round the cargo and clutter it
        stands among, on a lower deck) has no floor to judge by: None."""
        if not len(self.T):
            return None
        m = np.nonzero((self.lo[:, 0] <= x) & (x <= self.hi[:, 0]) & (self.lo[:, 1] <= y) & (y <= self.hi[:, 1]))[0]
        hs = [h for h in (_height_in(self.a[i], self.b[i], self.c[i], x, y) for i in m) if h is not None]
        if not hs:
            return None
        under = [h for h in hs if h <= z + tol]
        if under:
            return max(under)
        return min(hs) if z + tol < self.zmin else None

    def water(self, x, y):
        return None

    def centres(self) -> np.ndarray:
        return self.V[self.T].mean(axis=1) if len(self.T) else np.zeros((0, 3))

    def area(self) -> np.ndarray:
        return 0.5 * np.abs(np.cross(self.b - self.a, self.c - self.a)[:, 2]) if len(self.T) else np.zeros(0)


def _height_in(a, b, c, x, y):
    d = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
    if abs(d) < 1e-9:
        return None
    l1 = ((b[1] - c[1]) * (x - c[0]) + (c[0] - b[0]) * (y - c[1])) / d
    l2 = ((c[1] - a[1]) * (x - c[0]) + (a[0] - c[0]) * (y - c[1])) / d
    l3 = 1 - l1 - l2
    if min(l1, l2, l3) < -1e-6:
        return None
    return float(l1 * a[2] + l2 * b[2] + l3 * c[2])


def floor_of(navmesh_jsonl: Path, cut: dict | None = None, near: list | None = None, pad: float = 600.0) -> Floor:
    """The room's floor from its source cell's navmesh rows ({verts, tris: [[a, b, c, ...flags]]}): the triangles
    whose middle lies in the cut box (when the room is a cut), else within `pad` of the room's pieces' plan box `near`
    ([x1, y1, x2, y2]) when given."""
    V, T = [], []
    rows = [json.loads(x) for x in navmesh_jsonl.read_text().splitlines() if x.strip()] if navmesh_jsonl.exists() else []
    for r in rows:
        base = len(V)
        V += [list(map(float, v[:3])) for v in r.get("verts") or []]
        T += [[base + int(t[0]), base + int(t[1]), base + int(t[2])] for t in r.get("tris") or []]
    if not T:
        return Floor(np.zeros((0, 3)), np.zeros((0, 3), int))
    Va, Ta = np.asarray(V, float), np.asarray(T, int)
    C = Va[Ta].mean(axis=1)
    keep = np.ones(len(Ta), bool)
    box = None
    if cut and cut.get("box"):
        x1, y1, x2, y2 = cut["box"]
        box = [min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)]
    elif near is not None:
        box = [near[0] - pad, near[1] - pad, near[2] + pad, near[3] + pad]
    if box:
        keep = (box[0] <= C[:, 0]) & (C[:, 0] <= box[2]) & (box[1] <= C[:, 1]) & (C[:, 1] <= box[3])
    return Floor(Va, Ta[keep])


def flat_floor(z: float) -> Floor:
    """A room with no walkable mesh to read: no floor heights (nothing is called floating), its floor level z."""
    f = Floor(np.zeros((0, 3)), np.zeros((0, 3), int))
    f.floor = z
    return f


def spread(points: np.ndarray, n: int, weights: np.ndarray | None = None) -> np.ndarray:
    """n of the points spread over the floor (farthest-point sampling from the largest), for the void test."""
    P = np.asarray(points, float)
    if len(P) <= n:
        return P
    i0 = int(np.argmax(weights)) if weights is not None and len(weights) else 0
    got = [i0]
    d = np.linalg.norm(P[:, :2] - P[i0, :2], axis=1)
    while len(got) < n:
        i = int(np.argmax(d))
        got.append(i)
        d = np.minimum(d, np.linalg.norm(P[:, :2] - P[i, :2], axis=1))
    return P[got]


def walls(pieces: list[dict], eye: float = 112.0) -> list:
    """What a camera inside a room cannot stand behind: each door, and each tall thin piece of the shell (a wall, a
    pillar; not a floor or a whole-room piece), as plan boxes with the height band they fill."""
    from tools.places.look import geom
    out = []
    for p in pieces:
        if p.get("kind") not in ("door", "building", "static") or not p.get("model"):
            continue
        lo, hi = geom.aabb(p)
        thin = min(hi[0] - lo[0], hi[1] - lo[1]) < 600 and hi[2] - lo[2] > 150
        if p.get("kind") == "door" or thin:
            out.append((float(lo[0]), float(lo[1]), float(hi[0]), float(hi[1]), float(lo[2]), float(hi[2])))
    return out


def stand_inside(floor: Floor, target, toward, want: float, step: float = 24.0, blocks=(), eye: float = 112.0) -> float:
    """How far from `target` along the plan direction `toward` a camera may stand and still be over the room's floor,
    with no wall or door (`blocks`, from walls()) between: walked out from the target in steps while the floor goes on,
    at most `want` (the whole `want` when the room has no floor heights to read)."""
    if not len(floor.T):
        return want
    t = np.asarray(target[:2], float)
    u = np.asarray(toward[:2], float)
    u = u / max(float(np.linalg.norm(u)), 1e-9)
    blocks = [b for b in blocks if not (b[0] <= t[0] <= b[2] and b[1] <= t[1] <= b[3])]   # the subject's own
    last, s, misses = 0.0, step, 0
    while s <= want:
        x, y = t + u * s
        g = floor.height(x, y)
        if g is not None and any(b[0] <= x <= b[2] and b[1] <= y <= b[3] and b[4] <= g + eye <= b[5] for b in blocks):
            break
        if g is not None:
            last, misses = s, 0
        else:
            misses += 1
            if misses * step > 96:   # off the floor for more than a stride: a wall
                break
        s += step
    else:
        if misses == 0:   # the floor goes on past where the frame wants the camera
            return want
    return max(last - 32.0, min(want, 120.0) if last == 0 else 0.0)


def held_by_shell(faults: list[dict], pieces: list[dict], gap: float = 8.0) -> list[dict]:
    """A room's faults less the pieces a kit room holds by its walls: an arch, a bust in a niche, a beam set into the
    shell is fixed to the wall or pillar its box touches, as the room's kit is built; a piece that floats touching
    nothing of the shell still floats."""
    from tools.places.look import geom
    floating = {f["id"] for f in faults if f["fault"] == "floats"}
    shell = [geom.aabb(p) for p in pieces if p.get("kind") in ("building", "static") and p.get("model")
             and p["id"] not in floating]
    if not shell:
        return faults
    S0 = np.array([b[0] for b in shell])
    S1 = np.array([b[1] for b in shell])
    by = {p["id"]: p for p in pieces}
    out = []
    for f in faults:
        if f["fault"] == "floats" and f["id"] in by:
            lo, hi = geom.aabb(by[f["id"]])
            touch = ((S0[:, 0] - gap <= hi[0]) & (lo[0] <= S1[:, 0] + gap) & (S0[:, 1] - gap <= hi[1])
                     & (lo[1] <= S1[:, 1] + gap) & (S0[:, 2] - gap <= hi[2]) & (lo[2] <= S1[:, 2] + gap))
            if touch.any():   # something of the shell it is fixed to
                continue
        out.append(f)
    return out


COMPASS = ["east", "north-east", "north", "north-west", "west", "south-west", "south", "south-east"]


def heading(d) -> str:
    """A direction as words: a compass side, or up and down when it is mostly vertical."""
    x, y, z = (float(v) for v in d)
    if z > 0.8:
        return "up"
    if z < -0.8:
        return "down"
    return COMPASS[int(round(math.degrees(math.atan2(y, x)) / 45)) % 8] + (" and up" if z > 0.4 else " and down" if z < -0.4 else "")


def openings(looks: list[dict], box, min_frac: float = 0.012) -> list[dict]:
    """The void test's answers as openings: each look's faces that saw out (more than min_frac of a face), grouped by
    where the way out meets the room's plan box `box` ([x1, y1, x2, y2]: its cut, else its pieces), each with the
    floor points that see it and the direction."""
    found: dict = {}
    for lk in looks:
        p = np.asarray(lk["at"], float)
        for f in lk["out"]:
            if f["frac"] < min_frac:
                continue
            d = np.asarray(f["dir"], float)
            hit = _exit(p, d, box)
            key = (round(hit[0] / 256), round(hit[1] / 256), heading(d)) if hit is not None else ("up/down", heading(d))
            o = found.setdefault(key, {"towards": heading(d), "edge_at": None if hit is None else [round(v) for v in hit],
                                       "seen_from": [], "frac": 0.0})
            o["seen_from"].append([round(float(v)) for v in p])
            o["frac"] = round(max(o["frac"], f["frac"]), 3)
    return sorted(found.values(), key=lambda o: -o["frac"])


def _exit(p, d, box):
    """Where a ray from p along d leaves the plan box (None when it goes straight up or down)."""
    if abs(d[0]) < 1e-6 and abs(d[1]) < 1e-6:
        return None
    ts = []
    for k, (lo, hi) in enumerate(((box[0], box[2]), (box[1], box[3]))):
        if abs(d[k]) > 1e-6:
            ts += [(lo - p[k]) / d[k], (hi - p[k]) / d[k]]
    ts = [t for t in ts if t > 0]
    if not ts:
        return None
    q = p + d * min(ts)
    return [float(q[0]), float(q[1]), float(q[2])]
