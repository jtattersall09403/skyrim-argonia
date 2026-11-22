"""Every walk of a place is clear (owner, 2026-11-22): the world's road through it as the ground shows it, each
street, path, walkway, boardwalk or gangplank of its own (`paths.jsonl`), and the way from each door's outside
arrival to the nearest of them, free of every solid thing, unless a written reason says it is meant to stand there.

A blocker is any solid piece (classify: not a light, marker, sound, actor, groundcover, plant, effect or door, which
is walked through; the world's own rocks and trees about the place too) whose real shape (its mesh's surface cloud
in its pose, tools/places/shape.py) has a point between STEP and HEAD over the walked level, inside a way: lower is
stepped over (a rug, a root, a deck's own boards), higher is walked under (an arch, a roof, a sign).

- The world's road (`RoadPaint`): where the road's track textures show at least ROAD_SHARE on the ground, within
  the place's footprint and ROAD_REACH past it; the level is the ground; a deck or bridge over it is not a blocker.
- A path or door way: its corridor, half its width plus SHOULDER from its line; the level follows the line as it is
  walked, on the built walking mesh where the check has it, else our ground or a deck's own walked surface reached
  without a climb steeper than CLIMB a step (`levels`).

A creature's quest spot, and a person's fixed stop (any stop but wander, patrol and sleep, whose bed is furniture
and checked as a piece), inside a way is a blocker too: a walker would walk into it.

A blocker passes only with a reason: the ref's own `blocks_way` ("a toll gate meant to stop traffic"), or the
path's `blocked_by` {ref or spot id: reason} ("a barricade the quest clears"); either needs a sentence
(REASON_WORDS).

`check.check_streets` (the build's streets check, and so `draft check`) fails each blocker; `look <place> probe`
lists them under `ways`, with the point to look at.
"""
from __future__ import annotations

import math

import numpy as np

from tools.places import shape
from tools.places.classify import NO_SOLID_KINDS, effect, kind_of

SHOULDER = 32.0       # beyond the walking width either side: a walker's elbows and a pack
STEP = 24.0           # a thing lower than this over the walked level is stepped over
HEAD = 150.0          # a thing higher than this over it is walked under (a person is 126 tall)
SAMPLE = 32.0         # the line's level is read this often
CLIMB = 48.0          # a level change taken between two samples (a stair's run, a plank's rise); more is a drop
HOLD = 96.0           # a gap this long in a deck's walked surface is walked over at the deck's level
WADE = 40.0           # ground under water deeper than this is not walked
LEVEL_CLASSES = {"deck", "steps", "span", "boat"}    # what a walker walks on besides the ground
DOOR_WIDTH = 128.0    # the way from a door's arrival to the nearest walk
DOOR_GAP = 96.0       # a way that ends at a door: its own doorway and the wall about it are walked through
SPOT_R = 40.0         # a creature's or a person's own room on the ground
ROAD_SHARE = 0.45     # the world's road is where its track textures show at least this share (its feathered verge
#                       starts below it)
ROAD_REACH = 300.0    # the world's road is kept clear within the place's footprint and this far past it
ROAD_WAY = "the world's road"
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


def levels(S: np.ndarray, ground, decks: list) -> np.ndarray:
    """The walked level at each of a line's sample points: our ground (unless under water deeper than WADE) or the
    walked surface of a deck, a stair, a span or a boat (`decks`; never clutter or a crate's top): the one nearest
    the level before, except that a deck rising within CLIMB of it that goes on to the next sample is stepped onto
    (a rail's narrow top is not); over a gap in a deck's walked surface the level before holds for HOLD. The first
    sample: the ground, or a deck within CLIMB of it. Past HOLD over open water with nothing to stand on: NaN, not
    walked."""
    G, D = [], []
    for x, y in S:
        g = ground.height(x, y) if ground is not None else None
        w = ground.water(x, y) if ground is not None and hasattr(ground, "water") else None
        G.append((g, [] if g is None or (w is not None and w > g + WADE) else [g]))
        D.append([float(h) for h in (P.at(x, y, "walk") for P in decks) if h is not None and not math.isnan(h)])
    z = np.zeros(len(S))
    prev, held = None, 0.0
    for k in range(len(S)):
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


def _h(ground, x, y) -> float:
    h = ground.height(x, y) if ground is not None else None
    return float(h) if h is not None else math.nan


def _reason(text) -> bool:
    return len(str(text or "").split()) >= REASON_WORDS


def blockers(files: dict, pieces: list[dict], ground, spots: list[dict] = (), walked=None,
             road: RoadPaint | None = None) -> list[dict]:
    """Every solid thing or spot standing in a way: [{way, id, edid, kind, at: [x, y, z], from_middle, reason?}],
    one per (way, thing), at its point nearest the way's middle; `reason` set when it is allowed (and so not a
    fault). `walked(points)`: the built walking mesh's height at each sample point as the line is walked (None off
    it; `check.check_streets` gives `walk.Walkable.walked`); the levels are read from the pieces (`levels`) where it
    gives none, and everywhere without it (`look probe`)."""
    solid = [p for p in pieces if p.get("model") and p.get("resolved", True) and not p.get("missing")
             and (p.get("kind") or "") not in NO_SOLID_KINDS | {"door"} and not effect(p)]
    posed = []
    for p in solid:
        try:
            posed.append((p, shape.posed(p)))
        except Exception:      # a model with no shape is reported by the probe's own rules, not here
            continue
    rows = {r["id"]: r for r in ((files.get("spaces") or {}).get("exterior") or {}).get("refs") or []}
    found = []
    for w in ways(files):
        L = np.asarray([q[:2] for q in w["points"]], float)
        half = w["width"] / 2 + SHOULDER
        lo, hi = L.min(0) - half, L.max(0) + half
        near = [(p, P) for p, P in posed if P.hi[0] >= lo[0] and P.lo[0] <= hi[0] and P.hi[1] >= lo[1] and P.lo[1] <= hi[1]]
        S = np.asarray([q for _, q in _samples(w["points"])], float)
        Z = levels(S, ground, [P for p, P in near if kind_of(p) in LEVEL_CLASSES])
        if walked is not None:
            for k, h in enumerate(walked([tuple(q) for q in S])):
                if h is not None:
                    Z[k] = h
        for p, P in near:
            C = P.P
            if not len(C):
                continue
            m = (C[:, 0] >= lo[0]) & (C[:, 0] <= hi[0]) & (C[:, 1] >= lo[1]) & (C[:, 1] <= hi[1])
            C = C[m]
            if not len(C):
                continue
            d = _dist_to_line(C[:, :2], L)
            keep = d <= half
            for q in w.get("doors") or []:
                keep &= np.hypot(C[:, 0] - q[0], C[:, 1] - q[1]) > DOOR_GAP
            C, d = C[keep], d[keep]
            if not len(C):
                continue
            k = np.argmin(((C[:, None, :2] - S[None, :, :2]) ** 2).sum(-1), axis=1)
            over = C[:, 2] - Z[k]
            hit = np.isfinite(over) & (over >= STEP) & (over <= HEAD)
            if not hit.any():
                continue
            i = int(np.argmin(np.where(hit, d, np.inf)))
            row = rows.get(p["id"]) or {}
            why = row.get("blocks_way") or (w.get("blocked_by") or {}).get(p["id"])
            found.append({"way": w["id"], "id": p["id"], "edid": p.get("edid"), "kind": p.get("kind"),
                          "at": [round(float(v)) for v in C[i]], "from_middle": round(float(d[i])),
                          "world": bool(p.get("world")), "reason": why if _reason(why) else None})
        for s in spots:
            x, y = s["pos"][:2]
            dd = float(_dist_to_line(np.asarray([[x, y]], float), L)[0])
            if dd <= half + SPOT_R:
                why = (w.get("blocked_by") or {}).get(s["id"])
                found.append({"way": w["id"], "id": s["id"], "edid": s.get("what"), "kind": "spot",
                              "at": [round(v) for v in s["pos"][:3]], "from_middle": round(dd), "world": False,
                              "reason": why if _reason(why) else None})
    place = files.get("place") or {}
    anchor = (place.get("fit") or {}).get("anchor")
    reach = float(place.get("radius_m") or 50) * 70.0 + ROAD_REACH
    if road is not None and road.share and anchor:    # the world's road as painted, through the place: kept clear
        for p, P in posed:
            if math.dist(((P.lo[0] + P.hi[0]) / 2, (P.lo[1] + P.hi[1]) / 2), anchor) > reach:
                continue
            if kind_of(p) in LEVEL_CLASSES:     # a bridge or deck over the road is walked on or under
                continue
            C = P.P
            if not len(C):
                continue
            C = C[road.on(C[:, :2])]
            if not len(C):
                continue
            g = np.fromiter((_h(ground, x, y) for x, y in C[:, :2]), float, len(C))
            over = C[:, 2] - g
            band = np.isfinite(over) & (over >= STEP) & (over <= HEAD)
            if not band.any():
                continue
            q = C[band]
            k = int(np.argmax(road.many(q)))
            why = (rows.get(p["id"]) or {}).get("blocks_way")
            found.append({"way": ROAD_WAY, "id": p["id"], "edid": p.get("edid"), "kind": p.get("kind"),
                          "at": [round(float(v)) for v in q[k]], "from_middle": 0, "world": bool(p.get("world")),
                          "reason": why if _reason(why) else None})
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


def faults(files: dict, pieces: list[dict], ground, walked=None, road: RoadPaint | None = None) -> list[str]:
    return [line(b) for b in blockers(files, pieces, ground, spots(files), walked, road) if not b.get("reason")]


def place_faults(place_id: str, places=None, bundles=None, walked=None) -> list[str]:
    """`faults` over the committed place files: its exterior rows (and the world's rows about it) as pieces, over
    its ground with its land patches."""
    from tools.places import edits
    from tools.places.draft import io
    from tools.places.draft.obvious import piece, _seen
    from tools.places.look import geom as look
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
    bases = io.place_bases(src, grd, place)
    bases.update(io.catalogue_bases({r["base"] for r in refs + list(wrefs) if r.get("base")} - set(bases)))
    G = Ground.load(grd.path)
    G.apply_patches(files.get("land") or [])
    pieces = [piece(r, bases) for r in refs]
    world = [dict(p, world=True) for p in (piece(r, bases) for r in look.world_rows(wrefs, bases)) if p.get("resolved")]
    return faults(files, pieces + world, G, walked, road_paint(place_id, bundles))
