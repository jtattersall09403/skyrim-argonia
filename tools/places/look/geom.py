"""The look tool's pure parts: pieces as oriented boxes, camera framing and projection, the section line, picking,
and probe's rules (floating, unsupported ends, a door with no ground before it). No files, no browser.

Coordinates are the game's: units (70 to the metre), X east, Y north, Z up. A piece is a dict
{id, base, kind, cluster, edid, model, resolved, m (4x4 row-major model->world), lo, hi (model-space bounds)}.
"""
from __future__ import annotations

import math

import numpy as np

UNITS_PER_M = 70.0
EYE = 112.0                 # a person's eye over the ground (1.6 m)
PERSON = 126.0              # a person's height (1.8 m)
FLOAT_TOL = 24.0            # a piece's lowest point this far over the ground under it, with nothing under it: floats
END_TOL = 48.0              # a bridge or walkway end this far over the ground with nothing under it: unsupported
DOOR_TOL = 64.0             # the ground before a door within this of the door's sill: walkable
SIDES = {"n": 90.0, "ne": 45.0, "e": 0.0, "se": -45.0, "s": -90.0, "sw": -135.0, "w": 180.0, "nw": 135.0}
ELEV = {"eye": None, "oblique": 32.0, "high": 60.0, "top": 89.0}
SPAN_WORDS = ("bridge", "walkway", "dock", "boardwalk", "pier", "plank", "gangway", "stair", "ramp", "deck")
HANG_WORDS = ("lantern", "sconce", "rope", "chain", "hang", "banner", "sign", "lamp", "bell", "cage", "net", "candle")
STRUCTURAL = {"building", "static", "furniture", "door", "container", "activator"}
BURIED = 64.0              # a piece whose top is this far under the ground is lost in it
REACH = 160.0               # a supporter's top may rise this far past what rests on it (a post through a deck)
NO_SOLID = {"light", "marker", "sound", "actor", "groundcover", "plant"}


# ---------- pieces ----------
def corners(p: dict) -> np.ndarray:
    """The 8 world corners of a piece's box."""
    lo, hi, m = p["lo"], p["hi"], np.asarray(p["m"], float)
    pts = np.array([[x, y, z, 1.0] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])])
    return (m @ pts.T).T[:, :3]


def aabb(p: dict) -> tuple[np.ndarray, np.ndarray]:
    c = corners(p)
    return c.min(0), c.max(0)


def bottom_points(p: dict, n: int = 3) -> np.ndarray:
    """n x n points over the bottom face of a piece's box, in the world: its feet as the box knows them."""
    lo, hi, m = p["lo"], p["hi"], np.asarray(p["m"], float)
    pts = [[lo[0] + (hi[0] - lo[0]) * i / (n - 1), lo[1] + (hi[1] - lo[1]) * j / (n - 1), lo[2], 1.0]
           for i in range(n) for j in range(n)]
    return (m @ np.array(pts).T).T[:, :3]


def end_points(p: dict) -> np.ndarray:
    """The bottom middles of a span's two ends (along its longer model axis), in the world."""
    lo, hi, m = p["lo"], p["hi"], np.asarray(p["m"], float)
    cx, cy = (lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2
    if hi[0] - lo[0] >= hi[1] - lo[1]:
        pts = [[lo[0], cy, lo[2], 1.0], [hi[0], cy, lo[2], 1.0]]
    else:
        pts = [[cx, lo[1], lo[2], 1.0], [cx, hi[1], lo[2], 1.0]]
    return (m @ np.array(pts).T).T[:, :3]


def is_span(p: dict) -> bool:
    words = f"{p.get('edid') or ''} {p.get('model') or ''}".lower()
    return any(w in words for w in SPAN_WORDS)


def effect(p: dict) -> bool:
    """A game effect (mist, fire, a waterfall's spray): the studio draws none and nothing need hold it up."""
    m, e = str(p.get("model") or "").lower().replace("\\", "/"), str(p.get("edid") or "").lower()
    return m.startswith("effects/") or e.startswith("fx")


def hangs(p: dict) -> bool:
    words = f"{p.get('edid') or ''} {p.get('model') or ''}".lower()
    return any(w in words for w in HANG_WORDS)


def solid(p: dict) -> bool:
    return bool(p.get("resolved")) and p.get("kind") not in NO_SOLID


def support_under(pieces: list[dict], x: float, y: float, z: float, tol: float, skip: str | None = None,
                  boxes: dict | None = None) -> str | None:
    """A solid piece whose box holds (x, y) and reaches up to within tol of z from below: what holds z up."""
    for q in pieces:
        if q["id"] == skip or not solid(q):
            continue
        lo, hi = boxes[q["id"]] if boxes else aabb(q)
        if lo[0] - 1 <= x <= hi[0] + 1 and lo[1] - 1 <= y <= hi[1] + 1 and hi[2] >= z - tol and lo[2] < z - 1:
            return q["id"]
    return None


# ---------- probe ----------
def probe_piece(p: dict, ground, pieces: list[dict], boxes: dict | None = None) -> dict:
    """One piece's numbers: its box, each foot's height over the ground (negative: buried), what holds it up."""
    boxes = boxes or {q["id"]: aabb(q) for q in pieces}
    lo, hi = boxes[p["id"]]
    feet = []
    for x, y, z in bottom_points(p):
        g = ground.height(x, y)
        w = ground.water(x, y) if hasattr(ground, "water") else None
        feet.append({"at": [round(x, 1), round(y, 1)], "z": round(z, 1), "ground": None if g is None else round(g, 1),
                     "over": None if g is None else round(z - g, 1), "water": None if w is None else round(w, 1)})
    known = [f["over"] for f in feet if f["over"] is not None]
    low = float(lo[2])
    gmax = max((f["ground"] for f in feet if f["ground"] is not None), default=None)
    sup = support_under(pieces, (lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, low, FLOAT_TOL, p["id"], boxes) \
        or next((s for x, y, z in bottom_points(p) for s in [support_under(pieces, x, y, low, FLOAT_TOL, p["id"], boxes)] if s), None)
    out = {"id": p["id"], "base": p.get("base"), "edid": p.get("edid"), "kind": p.get("kind"), "cluster": p.get("cluster"),
           "model": p.get("model"), "resolved": bool(p.get("resolved")),
           "box": [[round(float(v), 1) for v in lo], [round(float(v), 1) for v in hi]],
           "lowest_over_ground": None if gmax is None else round(low - gmax, 1),
           "feet_over_ground": [min(known), max(known)] if known else None, "feet": feet, "held_by": sup}
    if is_span(p):
        out["ends"] = [end_report(e, ground, pieces, p["id"], boxes) for e in end_points(p)]
    if p.get("kind") == "door":
        out["door_ground"] = door_report(p, ground, pieces, boxes)
    near = []
    for q in pieces:
        if q["id"] == p["id"] or not solid(q):
            continue
        qlo, qhi = boxes[q["id"]]
        gap = box_gap(lo, hi, qlo, qhi)
        if gap < 400:
            near.append((gap, q["id"]))
    out["neighbours"] = [{"id": i, "gap": round(g, 1)} for g, i in sorted(near)[:4]]
    return out


def box_gap(alo, ahi, blo, bhi) -> float:
    """The distance between two boxes; negative: how deep they overlap (the least of the axes)."""
    d = [max(blo[i] - ahi[i], alo[i] - bhi[i]) for i in range(3)]
    return max(d) if max(d) < 0 else math.sqrt(sum(max(v, 0.0) ** 2 for v in d))


def end_report(e, ground, pieces, skip, boxes) -> dict:
    x, y, z = (float(v) for v in e)
    g = ground.height(x, y)
    held = support_under(pieces, x, y, z, END_TOL, skip, boxes)
    over = None if g is None else round(z - g, 1)
    return {"at": [round(x, 1), round(y, 1), round(z, 1)], "over_ground": over, "held_by": held,
            "supported": held is not None or (over is not None and over <= END_TOL)}


def door_report(p, ground, pieces, boxes) -> dict:
    """The ground where one comes out of the door (its arrival point, else 100 units each way along its model y)."""
    lo = boxes[p["id"]][0]
    sill = float(lo[2])
    arr = (p.get("door") or {}).get("arrival")
    pts = [arr[:2]] if arr else [[float(v) for v in (np.asarray(p["m"], float) @ np.array([0, s, p["lo"][2], 1.0]))[:2]]
                                 for s in (-100.0, 100.0)]
    best = None
    for x, y in pts:
        g = ground.height(x, y)
        held = support_under(pieces, x, y, sill + DOOR_TOL, 2 * DOOR_TOL, p["id"], boxes)
        ok = held is not None or (g is not None and abs(sill - g) <= DOOR_TOL)
        r = {"at": [round(x, 1), round(y, 1)], "ground": None if g is None else round(g, 1), "sill": round(sill, 1),
             "held_by": held, "walkable": ok}
        if best is None or ok:
            best = r
        if ok:
            break
    return best


class Boxes:
    """The solid pieces' world boxes as arrays, for asking what stands under a point."""
    def __init__(self, pieces: list[dict], boxes: dict):
        keep = [q for q in pieces if solid(q)]
        self.ids = [q["id"] for q in keep]
        self.lo = np.array([boxes[i][0] for i in self.ids]).reshape(-1, 3)
        self.hi = np.array([boxes[i][1] for i in self.ids]).reshape(-1, 3)
        # a tree holds nothing up from below; a Hist's great roots are walked on like ground (furniture stands on them)
        self.tree = np.array([q.get("kind") == "tree" and "root" not in str(q.get("edid") or "").lower() for q in keep], bool)

    def _over(self, x, y):
        lo, hi = self.lo, self.hi
        return (lo[:, 0] - 1 <= x) & (x <= hi[:, 0] + 1) & (lo[:, 1] - 1 <= y) & (y <= hi[:, 1] + 1)

    def under(self, x: float, y: float, z: float, tol: float, reach: float = None) -> np.ndarray:
        """Indexes of the boxes holding (x, y) whose top is within tol under z to `reach` over it (a post or wall
        that rises a little past a deck's underside holds it; a house whose roof is far above does not); a tree
        holds nothing up from below."""
        lo, hi = self.lo, self.hi
        reach = REACH if reach is None else reach
        return np.nonzero(self._over(x, y) & (hi[:, 2] >= z - tol) & (hi[:, 2] <= z + reach) & (lo[:, 2] < z - 1)
                          & ~self.tree)[0]

    def around(self, x: float, y: float, z: float) -> np.ndarray:
        """Indexes of the boxes (trees too) that reach past z both ways at (x, y): what a hanging thing hangs from."""
        lo, hi = self.lo, self.hi
        return np.nonzero(self._over(x, y) & (lo[:, 2] < z) & (hi[:, 2] > z))[0]


def grounding(pieces: list[dict], ground, boxes: dict | None = None, tol: float = FLOAT_TOL, world=()) -> dict:
    """For each drawn piece: its lowest point's height over the ground under it, what it rests on, and whether a
    chain of resting reaches the ground (a deck on posts on the ground is grounded; a deck on a deck in the air is not).
    `world`: the world's own things about the place (its trees, rocks): each holds up what rests on it."""
    boxes = boxes or {q["id"]: aabb(q) for q in pieces}
    for q in world:
        boxes.setdefault(q["id"], aabb(q))
    B = Boxes(list(pieces) + list(world), boxes)
    info = {}
    for p in pieces:
        if not p.get("model") or p.get("missing") or not p.get("resolved") or p.get("kind") in ("light", "marker") or effect(p):
            continue
        lo, hi = boxes[p["id"]]
        low = float(lo[2])
        pts = bottom_points(p)
        gs = [g for g in (ground.height(x, y) for x, y, _ in pts) if g is not None]
        over = round(low - max(gs), 1) if gs else None
        on = set()
        if over is not None and over > tol:
            for x, y in [((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2)] + [(q[0], q[1]) for q in pts]:
                on.update(B.ids[i] for i in B.under(x, y, low, tol))
            if hangs(p):   # a lantern, a sconce, a sign: held by what its top hangs from
                on.update(B.ids[i] for i in B.around((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, float(hi[2])))
            if p.get("kind") not in STRUCTURAL:   # a flower, a vine, a pot: held by the trunk or wall it grows on or sits in
                on.update(B.ids[i] for i in B.around((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, (low + float(hi[2])) / 2))
            on.discard(p["id"])
        info[p["id"]] = {"over": over, "low": round(low, 1), "on": sorted(on), "grounded": over is None or over <= tol}
    changed = True
    while changed:
        changed = False
        for i, r in info.items():
            if not r["grounded"] and any(info.get(j, {"grounded": True})["grounded"] for j in r["on"]):
                r["grounded"] = changed = True
    return info


def faults(pieces: list[dict], ground, world=()) -> list[dict]:
    """Every piece that floats (no chain of resting reaches the ground), every missing base and unresolved model,
    every span end with nothing under it, every door with no ground before it."""
    boxes = {q["id"]: aabb(q) for q in list(pieces) + list(world)}
    gr = grounding(pieces, ground, boxes, world=world)
    allp = list(pieces) + list(world)
    out = []
    for p in pieces:
        if p.get("kind") in ("marker", "light", "sound", "actor") and not p.get("model"):
            continue
        if p.get("missing"):
            out.append({"id": p["id"], "fault": "missing base", "base": p.get("base"), "cluster": p.get("cluster"),
                        "why": "its base is in no bundle: the studio draws nothing there and the build cannot place it"})
            continue
        if p.get("model") and not p.get("resolved"):
            out.append({"id": p["id"], "fault": "unresolved", "edid": p.get("edid"), "model": p.get("model"),
                        "cluster": p.get("cluster"), "why": "its model did not load: the studio shows a stand-in box"})
            continue
        if not p.get("model") or p.get("kind") in ("light", "marker"):
            continue
        g = gr.get(p["id"])
        top = float(boxes[p["id"]][1][2])
        hidden = "stolengoods" in str(p.get("edid") or "").lower()   # the Owing's stolen goods chest: under the ground by design
        if g and g["over"] is not None and top - (g["low"] - g["over"]) < -BURIED and not hidden:
            out.append({"id": p["id"], "fault": "buried", "edid": p.get("edid"), "cluster": p.get("cluster"),
                        "over": g["over"], "z": g["low"],
                        "why": f"its top is {g['low'] - g['over'] - top:.0f} units under the ground: nobody can see it"})
            continue
        def end_held(e):
            r = end_report(e, ground, allp, p["id"], boxes)
            return (r["held_by"] and gr.get(r["held_by"], {"grounded": True})["grounded"]) or \
                (r["over_ground"] is not None and r["over_ground"] <= END_TOL)
        # a bridge hung between two held ends (a rope bridge sagging between decks) floats over nothing in between
        slung = "bridge" in str(p.get("edid") or "").lower() and all(end_held(e) for e in end_points(p))
        if g and not g["grounded"] and not slung:
            sup = [i for i in g["on"]]
            out.append({"id": p["id"], "fault": "floats", "edid": p.get("edid"), "cluster": p.get("cluster"),
                        "over": g["over"], "z": g["low"], "on": sup[:4],
                        "why": f"its lowest point is {g['over']:.0f} units ({g['over'] / UNITS_PER_M:.1f} m) over the ground"
                        + (f", resting only on {len(sup)} piece(s) that do not reach the ground themselves" if sup else " with nothing under it")})
        if is_span(p):
            for e in end_points(p):
                r = end_report(e, ground, allp, p["id"], boxes)
                held = r["held_by"] and gr.get(r["held_by"], {"grounded": True})["grounded"]
                if not (held or (r["over_ground"] is not None and r["over_ground"] <= END_TOL)):
                    out.append({"id": p["id"], "fault": "unsupported end", "edid": p.get("edid"), "cluster": p.get("cluster"),
                                "at": r["at"], "over": r["over_ground"],
                                "why": f"an end at {r['at'][:2]} is {r['over_ground']} units over the ground with nothing under it"})
        if p.get("kind") == "door" and p.get("door"):
            r = door_report(p, ground, allp, boxes)
            if r and not r["walkable"]:
                out.append({"id": p["id"], "fault": "no ground at door", "edid": p.get("edid"), "cluster": p.get("cluster"),
                            "at": r["at"], "why": f"the ground before it is at {r['ground']}, its sill at {r['sill']}, nothing to stand on"})
    return out


# ---------- camera ----------
def nice(v: float, steps=(1, 2, 5)) -> float:
    """The round number at or under v (1, 2, 5 x 10^k)."""
    if v <= 0:
        return 1.0
    e = 10 ** math.floor(math.log10(v))
    return max(s * e for s in steps if s * e <= v) if any(s * e <= v for s in steps) else e


def frame(lo, hi, side: str = "se", height: str = "oblique", w: int = 768, h: int = 576, fov: float = 50.0,
          ground_z: float | None = None, fill: float = 0.85) -> dict:
    """A perspective camera that fills the frame with the box [lo, hi] seen from a compass side. Returns
    {pos, target, up, fov, w, h}. `eye`: from a person's eye over the ground, looking at the box's middle."""
    lo, hi = np.asarray(lo, float), np.asarray(hi, float)
    c = (lo + hi) / 2
    r = max(float(np.linalg.norm(hi - lo)) / 2, 60.0)
    vf = math.radians(fov) / 2
    hf = math.atan(math.tan(vf) * w / h)
    d = r / math.sin(min(vf, hf)) / fill
    az = math.radians(SIDES[side])
    gz = float(lo[2]) if ground_z is None else ground_z
    if height == "eye":
        horiz = max(d, r * 1.2)
        pos = np.array([c[0] + horiz * math.cos(az), c[1] + horiz * math.sin(az), gz + EYE])
        tgt = np.array([c[0], c[1], max(gz + EYE * 0.6, min(c[2], gz + EYE + horiz * 0.25))])
    else:
        el = math.radians(ELEV[height])
        pos = c + d * np.array([math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)])
        tgt = c
    up = [0.0, 1.0, 0.0] if height == "top" else [0.0, 0.0, 1.0]
    if height == "top":
        pos = np.array([c[0], c[1], c[2] + d])
    return {"pos": [round(float(v), 2) for v in pos], "target": [round(float(v), 2) for v in tgt], "up": up,
            "fov": fov, "w": w, "h": h,
            # nothing past a few subject widths behind it is drawn: the software rasteriser pays per triangle
            "far": round(d + 3 * r + 2000)}


def axes(cam: dict) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """The camera's right, up and back (three.js lookAt: back = pos - target)."""
    pos, tgt = np.asarray(cam["pos"], float), np.asarray(cam["target"], float)
    z = pos - tgt
    z /= np.linalg.norm(z)
    up = np.asarray(cam.get("up") or [0, 0, 1], float)
    x = np.cross(up, z)
    if np.linalg.norm(x) < 1e-6:
        x = np.cross([0.0, 1.0, 0.0], z)
    x /= np.linalg.norm(x)
    y = np.cross(z, x)
    return x, y, z


def project(cam: dict, pts) -> np.ndarray:
    """World points to pixels [px, py, depth] (depth > 0 in front of the camera)."""
    P = np.atleast_2d(np.asarray(pts, float)) - np.asarray(cam["pos"], float)
    x, y, z = axes(cam)
    cx, cy, cz = P @ x, P @ y, P @ z
    w, h = cam["w"], cam["h"]
    if cam.get("ortho"):
        nx, ny, depth = cx / cam["ortho"]["halfW"], cy / cam["ortho"]["halfH"], -cz
    else:
        t = math.tan(math.radians(cam.get("fov", 50.0)) / 2)
        depth = -cz
        with np.errstate(divide="ignore", invalid="ignore"):
            nx = cx / (np.where(depth == 0, 1e-9, depth) * t * w / h)
            ny = cy / (np.where(depth == 0, 1e-9, depth) * t)
    return np.stack([(nx + 1) / 2 * w, (1 - ny) / 2 * h, depth], axis=1)


def ray(cam: dict, px: float, py: float) -> tuple[np.ndarray, np.ndarray]:
    """The ray through a pixel: origin and unit direction."""
    x, y, z = axes(cam)
    w, h = cam["w"], cam["h"]
    nx, ny = px / w * 2 - 1, 1 - py / h * 2
    if cam.get("ortho"):
        o = np.asarray(cam["pos"], float) + x * nx * cam["ortho"]["halfW"] + y * ny * cam["ortho"]["halfH"]
        return o, -z
    t = math.tan(math.radians(cam.get("fov", 50.0)) / 2)
    d = -z + x * nx * t * w / h + y * ny * t
    return np.asarray(cam["pos"], float), d / np.linalg.norm(d)


def ray_box(o, d, p: dict) -> float | None:
    """Distance along the ray to a piece's box (in its own frame), or None."""
    m = np.asarray(p["m"], float)
    inv = np.linalg.inv(m)
    lo_ = inv @ np.append(o, 1.0)
    ld = inv[:3, :3] @ d
    t0, t1 = -math.inf, math.inf
    for i in range(3):
        if abs(ld[i]) < 1e-12:
            if not (p["lo"][i] <= lo_[i] <= p["hi"][i]):
                return None
            continue
        a, b = (p["lo"][i] - lo_[i]) / ld[i], (p["hi"][i] - lo_[i]) / ld[i]
        t0, t1 = max(t0, min(a, b)), min(t1, max(a, b))
    if t1 < max(t0, 0):
        return None
    s = max(t0, 0)
    return float(s * np.linalg.norm(m[:3, :3] @ ld) / max(np.linalg.norm(d), 1e-12))


def pick(cam: dict, px: float, py: float, pieces: list[dict], clip=None) -> list[tuple[float, dict]]:
    """Pieces under a pixel, nearest first (their boxes; the smallest box wins a near tie: the thing, not the
    building around it). clip: planes [nx, ny, nz, d] a hit point must keep (n.p + d >= 0)."""
    o, d = ray(cam, px, py)
    hits = []
    for p in pieces:
        if not p.get("model"):
            continue
        t = ray_box(o, d, p)
        if t is None or t <= 0:   # no hit, or the eye is inside the box (a tree's crown about the camera): not what is seen
            continue
        if clip:
            # a section's slab: the hit must lie within it; walk the box until it does
            lo, hi = aabb(p)
            if not any(all(np.dot(pl[:3], q) + pl[3] >= -1 for pl in clip) for q in _along(o, d, t, float(np.linalg.norm(hi - lo)))):
                continue
        vol = float(np.prod(np.subtract(p["hi"], p["lo"])))
        hits.append((t, vol, p))
    hits.sort(key=lambda h: (round(h[0] / 64), h[1]))
    return [(t, p) for t, _, p in hits]


def _along(o, d, t, span):
    return [o + d * (t + span * k / 8) for k in range(9)]


# ---------- section ----------
def section_camera(a, b, zlo: float, zhi: float, w: int = 768, h: int = 576, slab: float = 96.0, margin: float = 0.08) -> dict:
    """An orthographic camera looking square at the vertical plane through a-b (from its left side, so a is on the
    left), at one scale both ways, with the slab of the world within `slab` units of the plane kept."""
    a, b = np.asarray(a[:2], float), np.asarray(b[:2], float)
    t = b - a
    L = float(np.linalg.norm(t))
    t /= L
    n = np.array([t[1], -t[0]])            # the right of the line: the camera stands there and looks left
    mid = (a + b) / 2
    zc = (zlo + zhi) / 2
    upp = max(L * (1 + 2 * margin) / w, (zhi - zlo) * (1 + 2 * margin) / h)   # units per pixel
    pos = [mid[0] - n[0] * 50000, mid[1] - n[1] * 50000, zc]
    cam = {"pos": [float(v) for v in pos], "target": [float(mid[0]), float(mid[1]), float(zc)], "up": [0, 0, 1],
           "w": w, "h": h, "ortho": {"halfW": upp * w / 2, "halfH": upp * h / 2}, "near": 50000 - slab - 64, "far": 50000 + slab + 64,   # only the slab is drawn
           "clip": [[float(n[0]), float(n[1]), 0.0, float(-(n @ mid) + slab)],
                    [float(-n[0]), float(-n[1]), 0.0, float((n @ mid) + slab)]],
           "line": [a.tolist(), b.tolist()], "upp": upp, "slab": slab}
    # project() looks along -back: make sure a lands left of b
    pa, pb = project(cam, [[*a, zc], [*b, zc]])
    if pa[0] > pb[0]:
        cam["pos"] = [mid[0] + n[0] * 50000, mid[1] + n[1] * 50000, zc]
    return cam


def crosses(p: dict, a, b, slab: float, box=None) -> bool:
    """Whether a piece's footprint comes within slab of the segment a-b (its box corners, in plan)."""
    lo, hi = box if box is not None else aabb(p)
    a, b = np.asarray(a[:2], float), np.asarray(b[:2], float)
    t = b - a
    L = float(np.linalg.norm(t))
    t /= L
    n = np.array([-t[1], t[0]])
    c = corners(p)[:, :2] - a
    along, off = c @ t, c @ n
    return along.max() >= 0 and along.min() <= L and off.max() >= -slab and off.min() <= slab


def profile(ground, a, b, step: float = 32.0) -> list[tuple[float, float | None, float | None]]:
    """(distance along, ground height, water height) every step along a-b."""
    a, b = np.asarray(a[:2], float), np.asarray(b[:2], float)
    L = float(np.linalg.norm(b - a))
    n = max(2, int(L / step) + 1)
    out = []
    for i in range(n):
        s = L * i / (n - 1)
        x, y = a + (b - a) * (s / L)
        out.append((s, ground.height(x, y), ground.water(x, y) if hasattr(ground, "water") else None))
    return out


def long_axis(p: dict, extra: float = 300.0):
    """A line through a piece's (or box's) middle along its longer plan axis, past both ends."""
    lo, hi, m = p["lo"], p["hi"], np.asarray(p["m"], float)
    c = m @ np.array([(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, lo[2], 1.0])
    ax = np.array([1.0, 0, 0]) if hi[0] - lo[0] >= hi[1] - lo[1] else np.array([0, 1.0, 0])
    L = max(hi[0] - lo[0], hi[1] - lo[1]) / 2 + extra
    d = m[:3, :3] @ ax
    d = d[:2] / max(np.linalg.norm(d[:2]), 1e-9)
    return (c[:2] - d * L).tolist(), (c[:2] + d * L).tolist()


# ---------- walking ----------
def route(paths: list[list], a, b, join: float = 160.0) -> list[list[float]]:
    """The shortest way along the paths' polylines from the point nearest a to the point nearest b; points of
    different paths within `join` of each other are joined. [a, b] when there are no paths."""
    import heapq
    pts, edges = [], {}
    for line in paths:
        base = len(pts)
        pts += [list(map(float, q[:2])) for q in line]
        for i in range(len(line) - 1):
            edges.setdefault(base + i, []).append(base + i + 1)
            edges.setdefault(base + i + 1, []).append(base + i)
    if not pts:
        return [list(a[:2]), list(b[:2])]
    P = np.array(pts)
    for i in range(len(P)):
        d = np.linalg.norm(P - P[i], axis=1)
        for j in np.nonzero(d < join)[0]:
            if j != i:
                edges.setdefault(i, []).append(int(j))
    s = int(np.argmin(np.linalg.norm(P - np.asarray(a[:2]), axis=1)))
    t = int(np.argmin(np.linalg.norm(P - np.asarray(b[:2]), axis=1)))
    dist, prev, q = {s: 0.0}, {}, [(0.0, s)]
    while q:
        d0, u = heapq.heappop(q)
        if u == t:
            break
        if d0 > dist.get(u, math.inf):
            continue
        for v in edges.get(u, []):
            nd = d0 + float(np.linalg.norm(P[u] - P[v]))
            if nd < dist.get(v, math.inf):
                dist[v], prev[v] = nd, u
                heapq.heappush(q, (nd, v))
    if t not in dist:
        return [list(a[:2]), list(b[:2])]
    way = [t]
    while way[-1] != s:
        way.append(prev[way[-1]])
    return [list(a[:2])] + [pts[i] for i in reversed(way)] + [list(b[:2])]


def stations(way: list[list[float]], n: int = 6) -> list[tuple[list[float], list[float]]]:
    """n evenly spaced points along a polyline, each with the unit direction of travel there."""
    P = np.asarray(way, float)
    seg = np.linalg.norm(np.diff(P, axis=0), axis=1)
    L = float(seg.sum())
    if L == 0:
        return [(P[0].tolist(), [0.0, 1.0])] * n
    out = []
    cum = np.concatenate([[0], np.cumsum(seg)])
    for k in range(n):
        s = L * k / max(n - 1, 1) * 0.999
        i = int(np.searchsorted(cum, s, side="right") - 1)
        i = min(max(i, 0), len(seg) - 1)
        while seg[i] == 0 and i < len(seg) - 1:
            i += 1
        f = (s - cum[i]) / seg[i] if seg[i] else 0.0
        p = P[i] + (P[i + 1] - P[i]) * f
        d = (P[i + 1] - P[i]) / (seg[i] or 1.0)
        out.append((p.tolist(), d.tolist()))
    return out


def hull(points) -> list[tuple[float, float]]:
    """The convex hull of plan points (monotone chain), counter-clockwise."""
    pts = sorted(set((float(x), float(y)) for x, y in points))
    if len(pts) <= 2:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]
