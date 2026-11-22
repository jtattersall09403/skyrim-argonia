"""Every walk of a place is clear (owner, 2026-11-22): the world's road through it as the ground shows it, each
street, path, walkway, boardwalk or gangplank of its own (`paths.jsonl`), and the way from each door's outside
arrival to the nearest of them, free of every solid thing, unless a written reason says it is meant to stand there.

A blocker is any solid piece (classify: not a light, marker, sound, actor, groundcover, plant, effect or door, which
is walked through; not a hanging fixture, a ground piece walked on, nor moss, fern or vine; the world's own rocks and
trees about the place too) whose real shape (its mesh's surface cloud in its pose, tools/places/shape.py) has a
point between STEP and HEAD over the walked level, inside a way, where the built walking mesh runs under it: lower
is stepped over (a rug, a root, a deck's own boards), higher is walked under (an arch, a roof, a sign); a tree only
with its trunk and roots (to TRUNK); a thing past the mesh's edge (a fence, a rail, a post the mesh goes round) is
the walk's edge.

- The world's road (`RoadPaint`): where the road's track textures show at least ROAD_SHARE on the ground, within
  the place's footprint and ROAD_REACH past it; the level is the ground; a deck or bridge over it is not a blocker.
- A path or door way: its corridor, half its width plus SHOULDER from its line; the level follows the line as it is
  walked, on the built walking mesh where the check has it, else the line's own height, our ground or a deck's own
  walked surface reached without a climb steeper than CLIMB a step (`levels`). A deck, walkway, stair or ship the
  way runs on is its floor: its own rails and posts are the way's edges, not blockers.

A creature's quest spot, and a person's fixed stop (any stop but wander, patrol and sleep, whose bed is furniture
and checked as a piece), inside a way is a blocker too: a walker would walk into it.

A blocker passes only with a reason: the ref's own `blocks_way` ("a toll gate meant to stop traffic"), or the
path's `blocked_by` {ref or spot id: reason} ("a barricade the quest clears"); either needs a sentence
(REASON_WORDS).

`check.check_streets` (the build's streets check, and so `draft check`) fails each blocker; `look <place> probe`
lists them under `ways`, with the point to look at.

Staged as owed: the blockers found when the check came in (2026-11-22) are rows of OWED
(`newworld/places/ways_owed.jsonl`, one home: {place, way, id, edid, at, since, why?}): the check reports them as
owed, never failing; a blocker not in it fails; a row that no longer names a blocker is stale and fails until it is
deleted, so the list only shrinks; a row is never added after STAGED. A place hands over (`handover`) with no owed row
left, or each with a reason of a sentence (`why`).
"""
from __future__ import annotations

import math

import numpy as np
from scipy.spatial import cKDTree

from tools.places import shape
from tools.places.classify import NO_SOLID_KINDS, effect, has, kind_of

SHOULDER = 32.0       # beyond the walking width either side: a walker's elbows and a pack
STEP = 24.0           # a thing lower than this over the walked level is stepped over
HEAD = 150.0          # a thing higher than this over it is walked under (a person is 126 tall)
SAMPLE = 32.0         # the line's level is read this often
LINE_STEP = 8.0       # a point's distance from a way is read to the line's points this far apart
CLIMB = 48.0          # a level change taken between two samples (a stair's run, a plank's rise); more is a drop
HOLD = 96.0           # a gap this long in a deck's walked surface is walked over at the deck's level
WADE = 40.0           # ground under water deeper than this is not walked
LEVEL_CLASSES = {"deck", "steps", "span", "boat"}    # what a walker walks on besides the ground
NO_BODY_CLASSES = {"hanging fixture", "ground piece", "plant"}   # hung up, walked on, or walked through
NO_BODY_WORDS = ("moss", "fern", "vine", "ivy", "cobweb")         # draped and leafy things a walker brushes past
TRUNK = 64.0          # a tree blocks with its trunk and roots, this high over the walked level; its crown is passed under
DOOR_WIDTH = 128.0    # the way from a door's arrival to the nearest walk
DOOR_GAP = 96.0       # a way that ends at a door: its own doorway and the wall about it are walked through
SPOT_R = 40.0         # a creature's or a person's own room on the ground
ROAD_SHARE = 0.45     # the world's road is where its track textures show at least this share (its feathered verge
#                       starts below it)
ROAD_REACH = 300.0    # the world's road is kept clear within the place's footprint and this far past it
ROAD_WAY = "the world's road"
STAGED = "2026-11-22"   # the day the owed blockers were written; no row is added after it
CLEARED = 32.0        # a world plant within this of a cleared row of its base is the one the place switched off
REASON_WORDS = 6
FREE_STOPS = {"wander", "patrol", "sleep", "travel"}


class RoadPaint:
    """The world's roads as the ground shows them: the share of the road textures (any land texture whose name has
    `track`: the gravel and sand tracks the terrain lays its roads with) visible at each ground vertex, layers in
    order, each over the ones before (the 17 x 17 opacity grid of each 2048-unit quadrant). A road's bed is where
    that share is at least ROAD_SHARE."""

    QUAD = {"BottomLeft": (0, 0), "BottomRight": (1, 0), "TopLeft": (0, 1), "TopRight": (1, 1)}

    def __init__(self, share: dict):
        self.share = share
        if share:
            ij = np.asarray(list(share), int)
            self.i0, self.j0 = ij.min(0) - 1
            ni, nj = ij.max(0) - ij.min(0) + 3
            self.grid = np.zeros((ni, nj))
            for (i, j), v in share.items():
                self.grid[i - self.i0, j - self.j0] = v

    @classmethod
    def load(cls, terrain_json) -> "RoadPaint":
        import base64
        import json
        from pathlib import Path
        p = Path(terrain_json)
        if not p.exists():
            return cls({})
        d = json.loads(p.read_text())
        road = {k for k, v in (d.get("ltex") or {}).items() if "track" in str(v.get("edid") or "").lower()}
        share: dict = {}
        cells = d["cells"] if isinstance(d.get("cells"), list) else list((d.get("cells") or {}).values())
        for c in cells:
            quads: dict = {}
            for lay in c.get("layers") or []:
                quads.setdefault(lay["quad"], []).append(lay)
            for q, ls in quads.items():
                if not any(lay["tex"] in road for lay in ls):
                    continue
                qx, qy = cls.QUAD[q]
                cover, got = np.zeros(289), np.zeros(289)
                for lay in sorted(ls, key=lambda lay: lay["layer"], reverse=True):     # the top layer first
                    if lay["layer"] < 0:
                        a = np.ones(289)
                    elif lay.get("alpha"):
                        a = np.frombuffer(base64.b64decode(lay["alpha"]), np.uint8).astype(float)
                        a = a / 255.0
                    else:
                        continue
                    vis = a * (1 - cover)
                    if lay["tex"] in road:
                        got += vis
                    cover += vis
                for k in np.nonzero(got > 0.01)[0]:
                    r, cc = divmod(int(k), 17)
                    share[(c["cell"][0] * 32 + qx * 16 + cc, c["cell"][1] * 32 + qy * 16 + r)] = float(got[k])
        return cls(share)

    def at(self, x: float, y: float) -> float:
        """The road's share at a point, between the four ground vertices about it."""
        gx, gy = x / 128.0, y / 128.0
        i, j = math.floor(gx), math.floor(gy)
        fx, fy = gx - i, gy - j
        s = self.share
        return ((s.get((i, j), 0) * (1 - fx) + s.get((i + 1, j), 0) * fx) * (1 - fy)
                + (s.get((i, j + 1), 0) * (1 - fx) + s.get((i + 1, j + 1), 0) * fx) * fy)

    def many(self, XY: np.ndarray) -> np.ndarray:
        """`at` for many points at once."""
        if not self.share or not len(XY):
            return np.zeros(len(XY))
        g = np.asarray(XY, float)[:, :2] / 128.0
        i, j = np.floor(g[:, 0]).astype(int) - self.i0, np.floor(g[:, 1]).astype(int) - self.j0
        fx, fy = g[:, 0] - np.floor(g[:, 0]), g[:, 1] - np.floor(g[:, 1])
        ni, nj = self.grid.shape
        ok = (i >= 0) & (j >= 0) & (i < ni - 1) & (j < nj - 1)
        out = np.zeros(len(g))
        a, b, fx, fy = i[ok], j[ok], fx[ok], fy[ok]
        G = self.grid
        out[ok] = ((G[a, b] * (1 - fx) + G[a + 1, b] * fx) * (1 - fy) + (G[a, b + 1] * (1 - fx) + G[a + 1, b + 1] * fx) * fy)
        return out

    def on(self, XY: np.ndarray) -> np.ndarray:
        return self.many(XY) >= ROAD_SHARE


class NavGrid:
    """The built walking mesh outside (`navexport`'s `out/places/nav/<place>.json`): its main network (the largest
    set of joined dry triangles), as the heights of its triangles under a plan point (`heights`)."""
    B = 128.0

    def __init__(self, verts, tris, nb=None, kind=None):
        V = np.asarray(verts, float).reshape(-1, 3)
        T = np.asarray(tris, int).reshape(-1, 3)
        dry = np.ones(len(T), bool) if kind is None else (np.asarray(kind, int) != 2)
        keep = dry.copy()
        if nb is not None and len(T):
            N = np.asarray(nb, int).reshape(-1, 3)
            comp, best, cid = np.full(len(T), -1), (0, -1), 0
            for t0 in range(len(T)):
                if comp[t0] >= 0 or not dry[t0]:
                    continue
                stack, size = [t0], 0
                comp[t0] = cid
                while stack:
                    t = stack.pop()
                    size += 1
                    for u in N[t]:
                        if u >= 0 and comp[u] < 0 and dry[u]:
                            comp[u] = cid
                            stack.append(u)
                best = max(best, (size, cid))
                cid += 1
            keep = comp == best[1]
        self.T = V[T[keep]]
        lo = np.floor(self.T[:, :, :2].min(1) / self.B).astype(int)
        hi = np.floor(self.T[:, :, :2].max(1) / self.B).astype(int)
        self.bucket: dict = {}
        for k, (a, b) in enumerate(zip(lo, hi)):
            for i in range(a[0], b[0] + 1):
                for j in range(a[1], b[1] + 1):
                    self.bucket.setdefault((i, j), []).append(k)

    @classmethod
    def load(cls, path) -> "NavGrid | None":
        import json
        from pathlib import Path
        p = Path(path)
        if not p.exists():
            return None
        ext = (json.loads(p.read_text()).get("spaces") or {}).get("exterior")
        return cls(ext["verts"], ext["tris"], ext.get("nb"), ext.get("kind")) if ext else None

    def heights(self, x: float, y: float) -> list:
        out = []
        for k in self.bucket.get((math.floor(x / self.B), math.floor(y / self.B)), ()):
            a, b, c = self.T[k]
            d = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
            if abs(d) < 1e-9:
                continue
            l1 = ((b[1] - c[1]) * (x - c[0]) + (c[0] - b[0]) * (y - c[1])) / d
            l2 = ((c[1] - a[1]) * (x - c[0]) + (a[0] - c[0]) * (y - c[1])) / d
            if min(l1, l2, 1 - l1 - l2) >= -0.02:
                out.append(float(l1 * a[2] + l2 * b[2] + (1 - l1 - l2) * c[2]))
        return out


class WalkableMesh:
    """`check.check_streets`'s built mesh (`walk.Walkable`) as `NavGrid`'s `heights`: its main network's triangles
    under a point."""

    def __init__(self, W):
        self.W = W

    def heights(self, x: float, y: float) -> list:
        c, dp, z = self.W._cands((x, y), 2.0)
        return [float(h) for t, h in zip(c, z) if self.W.main[t]]


def _on_mesh(mesh, P: np.ndarray, Z: np.ndarray, top: np.ndarray | float = None, cell: float = 4.0) -> np.ndarray:
    """Whether each point stands in the walk on the built mesh: the mesh runs under it at about the walked level
    (within CLIMB of Z) and the point is between STEP and `top` (HEAD) over the mesh there. A thing past the mesh's
    edge (a fence, a rail, a post the mesh goes round) is the walk's edge; a surface the mesh runs on (a mound, a
    landscape trim, a root it crosses) is walked on."""
    top = np.full(len(P), HEAD) if top is None else np.broadcast_to(np.asarray(top, float), (len(P),))
    keys = np.floor(np.asarray(P, float)[:, :2] / cell).astype(np.int64)
    out = np.zeros(len(P), bool)
    seen: dict = {}
    for n, ((i, j), z) in enumerate(zip(keys, Z)):
        hs = seen.get((i, j))
        if hs is None:
            hs = seen[(i, j)] = mesh.heights(i * cell, j * cell)
        if not np.isfinite(z):
            continue
        near = [h for h in hs if abs(h - z) <= CLIMB]
        if near:
            over = P[n, 2] - min(near, key=lambda h: abs(h - z))
            out[n] = STEP <= over <= top[n]
    return out


def _mesh_levels(S: np.ndarray, mesh, Z: np.ndarray, given: list) -> np.ndarray:
    """The walked level on the built mesh at each sample: the mesh's height nearest the line's own height where it
    carries one, else nearest the level before (the first: nearest the level `levels` read); `levels`' value where
    the mesh has none."""
    out = Z.copy()
    prev = None
    for k, (x, y) in enumerate(S):
        hs = mesh.heights(x, y)
        ref = given[k] if given and given[k] is not None else (prev if prev is not None else Z[k])
        if hs and ref is not None and np.isfinite(ref):
            out[k] = min(hs, key=lambda h: abs(h - ref))
        prev = out[k] if np.isfinite(out[k]) else prev
    return out


def road_paint(place_id: str, bundles=None) -> RoadPaint:
    from tools.places.draft import io
    return RoadPaint.load((bundles or io.BUNDLES) / f"ground.{place_id}" / "spaces" / "exterior" / "terrain.json")


def ways(files: dict) -> list[dict]:
    """The place's ways: its paths (`paths.jsonl`) as they are, and for each outside door with an arrival, the way from its arrival to the nearest point of a path (when the door is
    not a path's own end)."""
    paths = [dict(p) for p in files.get("paths") or [] if len(p.get("points") or []) >= 2]
    ext = {r["id"]: r for r in ((files.get("spaces") or {}).get("exterior") or {}).get("refs") or []}
    out = [{"id": p["id"], "width": float(p.get("width") or 160.0), "points": [list(q) for q in p["points"]],
            "blocked_by": p.get("blocked_by") or {},
            "doors": [ext[p[k]]["pos"][:2] for k in ("from", "to") if (ext.get(p.get(k) or "") or {}).get("kind") == "door"]}
           for p in paths]
    ends = {p.get(k) for p in paths for k in ("from", "to")}
    lines = [np.asarray([q[:2] for q in p["points"]], float) for p in paths]
    for sid, sp in (files.get("spaces") or {}).items():
        if sid == "exterior":
            continue
        for r in sp.get("refs") or []:
            d = r.get("door") or {}
            out_door = ext.get(d.get("to_ref") or "")
            if not out_door or out_door["id"] in ends or not d.get("to_pos") or not lines:
                continue
            a = d["to_pos"]
            q = min((_nearest_on(L, a[:2]) for L in lines), key=lambda t: math.dist(t, a[:2]))
            if math.dist(q[:2], a[:2]) > 8:
                out.append({"id": f"door {out_door['id']}", "width": DOOR_WIDTH, "points": [list(a[:2]), list(q[:2])],
                            "blocked_by": {}, "doors": [out_door["pos"][:2]]})
    return out


def _nearest_on(L: np.ndarray, a) -> tuple[float, float]:
    """The point of the polyline L nearest to a, in plan."""
    best, got = math.inf, tuple(L[0])
    for u, v in zip(L, L[1:]):
        d = v - u
        t = min(1.0, max(0.0, float((np.asarray(a, float) - u) @ d) / (float(d @ d) or 1e-9)))
        q = u + t * d
        if math.dist(q, a) < best:
            best, got = math.dist(q, a), (float(q[0]), float(q[1]))
    return got


def _samples(pts: list, step: float = SAMPLE) -> list[tuple[int, tuple]]:
    out = []
    for i, (a, b) in enumerate(zip(pts, pts[1:])):
        n = max(1, math.ceil(math.dist(a[:2], b[:2]) / step))
        out += [(i, (a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n)) for k in range(n)]
    out.append((len(pts) - 2, tuple(pts[-1][:2])))
    return out


def _heights_given(pts: list, step: float = SAMPLE) -> list:
    """The line's own height at each sample where both ends of its stretch carry one (a walk laid on a deck at its
    own level), else None."""
    out = []
    for a, b in zip(pts, pts[1:]):
        n = max(1, math.ceil(math.dist(a[:2], b[:2]) / step))
        both = len(a) > 2 and len(b) > 2
        out += [(a[2] + (b[2] - a[2]) * k / n) if both else None for k in range(n)]
    out.append(pts[-1][2] if len(pts[-1]) > 2 and len(pts) > 1 and len(pts[-2]) > 2 else None)
    return out


def levels(S: np.ndarray, ground, decks: list, given: list | None = None) -> np.ndarray:
    """The walked level at each of a line's sample points: our ground (unless under water deeper than WADE) or the
    walked surface of a deck, a stair, a span or a boat (`decks`; never clutter or a crate's top): the one nearest
    the level before, except that a deck rising within CLIMB of it that goes on to the next sample is stepped onto
    (a rail's narrow top is not); over a gap in a deck's walked surface the level before holds for HOLD. The first
    sample: the ground, or a deck within CLIMB of it. Where the line carries its own height (`given`), the level
    nearest it. Past HOLD over open water with nothing to stand on: NaN, not walked."""
    G, D = [], []
    for x, y in S:
        g = ground.height(x, y) if ground is not None else None
        w = ground.water(x, y) if ground is not None and hasattr(ground, "water") else None
        G.append((g, [] if g is None or (w is not None and w > g + WADE) else [g]))
        D.append([float(h) for h in (P.at(x, y, "walk") for P in decks) if h is not None and not math.isnan(h)])
    z = np.zeros(len(S))
    prev, held = None, 0.0
    for k in range(len(S)):
        if given is not None and given[k] is not None:       # the line's own height is the level walked there
            z[k], prev, held = given[k], given[k], 0.0
            continue
        g, gnd = G[k]
        dk = D[k]
        nxt = D[k + 1] if k + 1 < len(S) else dk
        step = math.dist(S[k], S[k - 1]) if k else 0.0
        if not gnd and not dk and held + step > HOLD:     # open water with nothing to stand on: not walked here
            z[k], prev, held = math.nan, None, 0.0
            continue
        if prev is None:
            up = [c for c in dk if g is None or abs(c - g) <= CLIMB]
            z[k] = max(up) if up else (g if gnd else (min(dk) if dk else math.nan))
        else:
            near = [c for c in gnd + dk if abs(c - prev) <= CLIMB]
            rise = [c for c in dk if 0 < c - prev <= CLIMB and any(abs(c - n) <= CLIMB for n in nxt)]
            if rise:
                z[k], held = max(rise), 0.0
            elif near:
                z[k], held = min(near, key=lambda c: abs(c - prev)), 0.0
            elif held + step <= HOLD and not gnd:
                z[k], held = prev, held + step
            else:
                cands = gnd + dk
                z[k], held = (min(cands, key=lambda c: abs(c - prev)) if cands else prev), 0.0
        prev = z[k]
    return z


def _dist_to_line(XY: np.ndarray, L: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """(distance in plan from each point to the polyline L, the nearest point's position along L as a sample index
    fraction is not needed: the index of L's nearest vertex)."""
    best = np.full(len(XY), np.inf)
    for a, b in zip(L, L[1:]):
        d = b - a
        n2 = float(d @ d) or 1e-9
        t = np.clip(((XY - a) @ d) / n2, 0, 1)
        best = np.minimum(best, np.linalg.norm(XY - (a + t[:, None] * d), axis=1))
    return best


def _heights(ground, XY: np.ndarray, cell: float = 16.0) -> np.ndarray:
    """The ground's height under many points, read once per CELL square (a cloud has many points to a square)."""
    keys = np.floor(np.asarray(XY, float) / cell).astype(np.int64)
    uk, inv = np.unique(keys, axis=0, return_inverse=True)
    h = np.fromiter((_h(ground, (i + 0.5) * cell, (j + 0.5) * cell) for i, j in uk), float, len(uk))
    return h[np.asarray(inv).reshape(-1)]


def _h(ground, x, y) -> float:
    h = ground.height(x, y) if ground is not None else None
    return float(h) if h is not None else math.nan


def _reason(text) -> bool:
    return len(str(text or "").split()) >= REASON_WORDS


def blockers(files: dict, pieces: list[dict], ground, spots: list[dict] = (), mesh=None,
             road: RoadPaint | None = None) -> list[dict]:
    """Every solid thing or spot standing in a way: [{way, id, edid, kind, at: [x, y, z], from_middle, reason?}],
    one per (way, thing), at its point nearest the way's middle; `reason` set when it is allowed (and so not a
    fault). `mesh`: the built walking mesh (`NavGrid`, `WalkableMesh`): the walked level is read on it, and a thing
    counts only where the mesh runs under it (`_on_mesh`); without it (`look probe` before a build) the levels are
    read from the pieces (`levels`) and the way's width alone bounds it."""
    solid = [p for p in pieces if p.get("model") and p.get("resolved", True) and not p.get("missing")
             and (p.get("kind") or "") not in NO_SOLID_KINDS | {"door"} and not effect(p)
             and kind_of(p) not in NO_BODY_CLASSES and not has(p, NO_BODY_WORDS)]
    from tools.places.look.geom import aabb
    rows = {r["id"]: r for r in ((files.get("spaces") or {}).get("exterior") or {}).get("refs") or []}
    found = []

    def shaped(p):
        try:          # read once and let go after (a town's shapes do not all fit in memory at once)
            return shape.Posed(p)
        except Exception:  # a model with no shape is reported by the probe's own rules, not here
            return None
    # the ways first: each one's line, corridor, samples and walked levels (decks read for the levels only)
    W = []
    decks = [(p, aabb(p)) for p in solid if kind_of(p) in LEVEL_CLASSES]
    for w in ways(files):
        L = np.asarray([q[:2] for q in w["points"]], float)
        half = w["width"] / 2 + SHOULDER
        lo, hi = L.min(0) - half, L.max(0) + half
        S = np.asarray([q for _, q in _samples(w["points"])], float)
        given = _heights_given(w["points"])
        if mesh is not None:
            Z = _mesh_levels(S, mesh, levels(S, ground, [], given), given)
        else:
            dk = [P for P in (shaped(p) for p, (x, y) in decks
                              if y[0] >= lo[0] and x[0] <= hi[0] and y[1] >= lo[1] and x[1] <= hi[1]) if P is not None]
            Z = levels(S, ground, dk, given)
        W.append({"w": w, "L": L, "half": half, "lo": lo, "hi": hi, "S": S, "Z": Z, "Stree": cKDTree(S[:, :2]),
                  "line": cKDTree(np.asarray([q for _, q in _samples(w["points"], LINE_STEP)], float))})
        for s_ in spots:
            x, y = s_["pos"][:2]
            dd = float(_dist_to_line(np.asarray([[x, y]], float), L)[0])
            if dd <= half + SPOT_R:
                why = (w.get("blocked_by") or {}).get(s_["id"])
                found.append({"way": w["id"], "id": s_["id"], "edid": s_.get("what"), "kind": "spot",
                              "at": [round(v) for v in s_["pos"][:3]], "from_middle": round(dd), "world": False,
                              "reason": why if _reason(why) else None})
    place = files.get("place") or {}
    anchor = (place.get("fit") or {}).get("anchor")
    reach = float(place.get("radius_m") or 50) * 70.0 + ROAD_REACH
    on_road = road is not None and road.share and anchor
    # then each solid thing once: tested against the ways its box meets, and the road
    for p in solid:
        a_, b_ = aabb(p)
        mine = [v for v in W if b_[0] >= v["lo"][0] and a_[0] <= v["hi"][0] and b_[1] >= v["lo"][1] and a_[1] <= v["hi"][1]]
        roadside = bool(on_road) and kind_of(p) not in LEVEL_CLASSES and \
            math.dist(((a_[0] + b_[0]) / 2, (a_[1] + b_[1]) / 2), anchor) <= reach + max(b_[0] - a_[0], b_[1] - a_[1])
        if not mine and not roadside:
            continue
        P = shaped(p)
        if P is None:
            continue
        C0 = P.P
        top = TRUNK if kind_of(p) == "tree" else HEAD
        row = rows.get(p["id"]) or {}
        for v in mine:
            w, S, Z = v["w"], v["S"], v["Z"]
            if kind_of(p) in LEVEL_CLASSES and not row.get("blocks_way"):   # the deck the way runs on is its floor
                if any((h := P.at(x, y, "walk")) is not None and np.isfinite(z) and abs(h - z) <= 6
                       for (x, y), z in zip(S, Z)):
                    continue
            lo, hi, half = v["lo"], v["hi"], v["half"]
            C = C0[(C0[:, 0] >= lo[0]) & (C0[:, 0] <= hi[0]) & (C0[:, 1] >= lo[1]) & (C0[:, 1] <= hi[1])]
            if not len(C):
                continue
            d = v["line"].query(C[:, :2], distance_upper_bound=half + LINE_STEP)[0]
            keep = d <= half
            for q in w.get("doors") or []:
                keep &= np.hypot(C[:, 0] - q[0], C[:, 1] - q[1]) > DOOR_GAP
            C, d = C[keep], d[keep]
            if not len(C):
                continue
            k = v["Stree"].query(C[:, :2])[1]
            over = C[:, 2] - Z[k]
            hit = np.isfinite(over) & (over >= STEP) & (over <= top)
            if mesh is not None and hit.any():
                hit[hit] = _on_mesh(mesh, C[hit], Z[k][hit], top)
            if not hit.any():
                continue
            i = int(np.argmin(np.where(hit, d, np.inf)))
            why = row.get("blocks_way") or (w.get("blocked_by") or {}).get(p["id"])
            found.append({"way": w["id"], "id": p["id"], "edid": p.get("edid"), "kind": p.get("kind"),
                          "at": [round(float(x)) for x in C[i]], "from_middle": round(float(d[i])),
                          "world": bool(p.get("world")), "reason": why if _reason(why) else None})
        if roadside and len(C0):      # the world's road as painted, through the place: kept clear
            C = C0[road.on(C0[:, :2])]
            C = C[np.hypot(C[:, 0] - anchor[0], C[:, 1] - anchor[1]) <= reach] if len(C) else C
            if len(C):
                g = _heights(ground, C[:, :2])
                over = C[:, 2] - g
                band = np.isfinite(over) & (over >= STEP) & (over <= top)
                if mesh is not None and band.any():
                    band[band] = _on_mesh(mesh, C[band], g[band], top)
                if band.any():
                    q = C[band]
                    k = int(np.argmax(road.many(q)))
                    why = row.get("blocks_way")
                    found.append({"way": ROAD_WAY, "id": p["id"], "edid": p.get("edid"), "kind": p.get("kind"),
                                  "at": [round(float(x)) for x in q[k]], "from_middle": 0,
                                  "world": bool(p.get("world")), "reason": why if _reason(why) else None})
        del P, C0
    if on_road:
        for s_ in spots:
            if road.at(*s_["pos"][:2]) >= ROAD_SHARE and math.dist(s_["pos"][:2], anchor) <= reach:
                found.append({"way": ROAD_WAY, "id": s_["id"], "edid": s_.get("what"), "kind": "spot",
                              "at": [round(v) for v in s_["pos"][:3]], "from_middle": 0, "world": False,
                              "reason": None})
    return found


def spots(files: dict) -> list[dict]:
    """The creature spots of the place's quests and its people's fixed stops outside, as [{id, pos, what}]."""
    out = []
    for q in files.get("quests") or []:
        ref = str(q.get("ref") or "")
        if q.get("space", "exterior") == "exterior" and ref.startswith("npc.") and q.get("pos"):
            out.append({"id": q["id"], "pos": q["pos"], "what": f"quest spot {ref}"})
    for p in files.get("people") or []:
        for i, st in enumerate(p.get("routine") or []):
            at = st.get("at") or {}
            if st.get("kind") in FREE_STOPS or at.get("space", "exterior") != "exterior" or not at.get("pos"):
                continue
            if float(at.get("radius") or 0) > 2 * SPOT_R:      # a wide stop is walked about in, not stood on
                continue
            out.append({"id": f"{p['id']}#{i}", "pos": list(at["pos"]) + [0.0] * (3 - len(at["pos"])),
                        "what": f"{p.get('name') or p['id']}'s {st.get('kind')} stop"})
    return out


def line(b: dict) -> str:
    what = f"{b['id']} ({b.get('edid') or b.get('kind')}{', the world' + chr(39) + 's' if b.get('world') else ''})"
    return (f"way {b['way']}: {what} stands in the walk at {b['at'][:2]}, {b['from_middle']} units from its middle: "
            f"move it off the way, or give the reason it must stand there (`blocks_way` on the ref, or the way's "
            f"`blocked_by`)")


def faults(files: dict, pieces: list[dict], ground, mesh=None, road: RoadPaint | None = None) -> list[str]:
    return [line(b) for b in blockers(files, pieces, ground, spots(files), mesh, road) if not b.get("reason")]


def place_faults(place_id: str, places=None, bundles=None, mesh=None) -> list[str]:
    """`faults` over the committed place files: its exterior rows (and the world's rows about it) as pieces, over
    its ground with its land patches."""
    return [line(b) for b in _place_blockers(place_id, places, bundles, mesh) if not b.get("reason")]


def _place_blockers(place_id: str, places=None, bundles=None, mesh=None) -> list[dict]:
    from tools.places import edits
    from tools.places.draft import io
    from tools.places.draft.obvious import piece, _seen
    from tools.places.look import geom as look
    from pathlib import Path
    from tools.places.seat import Ground
    places = places or io.PLACES
    bundles = bundles or io.BUNDLES
    pdir = places / place_id
    files = edits.load_place(pdir)
    place = files["place"]
    src = io.load(f"src.{place['source_id']}", bundles)
    grd = io.load(f"ground.{place_id}", bundles)
    refs = [r for r in ((files["spaces"].get("exterior") or {}).get("refs") or []) if _seen(r)]
    wrefs = grd.exterior.refs if grd.exterior else []
    gone: dict = {}           # the world's plants the place switches off (clear.jsonl: base and nearest position)
    for c in files.get("clear") or []:
        gone.setdefault(c.get("base"), []).append(c.get("pos") or [0, 0, 0])
    if gone:
        wrefs = [r for r in wrefs if not any(math.dist(r["pos"][:2], q[:2]) <= CLEARED for q in gone.get(r.get("base"), ()))]
    bases = io.place_bases(src, grd, place)
    bases.update(io.catalogue_bases({r["base"] for r in refs + list(wrefs) if r.get("base")} - set(bases)))
    G = Ground.load(grd.path)
    G.apply_patches(files.get("land") or [])
    pieces = [piece(r, bases) for r in refs]
    world = [dict(p, world=True) for p in (piece(r, bases) for r in look.world_rows(wrefs, bases)) if p.get("resolved")]
    if mesh is None:      # the place's last built walking mesh, when it has one
        mesh = NavGrid.load(Path(bundles).parents[0] / "nav" / f"{place_id}.json")
    return blockers(files, pieces + world, G, spots(files), mesh, road_paint(place_id, bundles))


def place_blockers(place_id: str, places=None, bundles=None, mesh=None) -> list[dict]:
    """`blockers` over the committed place files (as `place_faults` reads them), unreasoned ones only."""
    return [b for b in _place_blockers(place_id, places, bundles, mesh) if not b.get("reason")]


def owed_path(places=None):
    from tools.places.draft import io
    return (places or io.PLACES) / "ways_owed.jsonl"


def owed(place_id: str, places=None) -> list[dict]:
    import json
    p = owed_path(places)
    if not p.exists():
        return []
    return [r for r in (json.loads(x) for x in p.read_text().splitlines() if x.strip()) if r.get("place") == place_id]


def _key(b: dict) -> tuple:
    return (b["way"], b["id"])


def split_owed(place_id: str, found: list[dict], places=None) -> tuple[list[dict], list[dict], list[str]]:
    """(failing blockers, owed blockers, the owed list's own faults): a blocker in the owed list is owed; a list row
    naming no blocker now is stale; a row written after STAGED is refused."""
    rows = owed(place_id, places)
    keys = {_key(r) for r in rows}
    fail = [b for b in found if _key(b) not in keys]
    got = [b for b in found if _key(b) in keys]
    now = {_key(b) for b in found}
    bad = [f"ways owed row {r['way']} / {r['id']} names no blocker now: delete it from {owed_path(places).name}"
           for r in rows if _key(r) not in now]
    bad += [f"ways owed row {r['way']} / {r['id']} was added after {STAGED}: a new blocker is mended, never owed"
            for r in rows if str(r.get("since") or "") != STAGED]
    return fail, got, bad


def write_owed(place_ids: list, places=None, bundles=None) -> dict:
    """Write the owed list from each place's blockers now (the staging, once): {place: rows}."""
    import json
    p = owed_path(places)
    keep = [json.loads(x) for x in p.read_text().splitlines() if x.strip()] if p.exists() else []
    keep = [r for r in keep if r.get("place") not in place_ids]
    got = {}
    for pid in place_ids:
        rows = [{"place": pid, "way": b["way"], "id": b["id"], "edid": b.get("edid"), "at": b["at"], "since": STAGED}
                for b in place_blockers(pid, places, bundles)]
        got[pid] = rows
        keep += rows
    keep.sort(key=lambda r: (r["place"], r["way"], r["id"]))
    p.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in keep))
    return got


def handover_line(place_id: str, places=None) -> tuple[bool, str]:
    """(passes, a line saying so): the place's owed blockers are cleared, or each has a reason of a sentence."""
    rows = owed(place_id, places)
    left = [r for r in rows if not _reason(r.get("why"))]
    if not left:
        return True, ("ways: nothing owed" if not rows else f"ways: {len(rows)} owed blocker(s), each with its reason")
    return False, (f"ways FAILS: {len(left)} owed blocker(s) stand in a road or walk with no reason "
                   f"({owed_path(places).name}): move each off its way, or give the reason it stands there")


def main(argv: list[str]) -> int:
    """`python -m tools.places ways <place_id>`: every unreasoned blocker in the place's road and walks, each marked
    owed (a row of the owed list) or failing, and the owed list's own faults (stale rows). 0 when nothing fails."""
    if len(argv) != 1:
        print("usage: python -m tools.places ways <place_id>")
        return 2
    pid = argv[0]
    fail, got, bad = split_owed(pid, place_blockers(pid))
    for b in got:
        print("owed  " + line(b))
    for b in fail:
        print("FAIL  " + line(b))
    for f in bad:
        print("FAIL  " + f)
    print(f"ways {pid}: {len(fail) + len(bad)} failing, {len(got)} owed")
    return 1 if fail or bad else 0
