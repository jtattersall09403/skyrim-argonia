"""Vegetation clearance: measured on the source, applied to our world's plants.

The source's clearance is how close its own plants come to what it built: for trees and for low plants
separately, the CLEAR_PCT percentile of each plant's distance to the nearest building footprint, street and
doorway, over the plants within the town's reach. Our world's plants (ground bundle refs of layer `world`) closer
than that to what we placed are switched off in clear.jsonl; anything standing inside a footprint, on a street or
in a doorway is always cleared.
"""
from __future__ import annotations

from tools.places.draft import geom
from tools.places.draft.cluster import rect_dist
from tools.places.draft.paths import dist_to_paths

CLEAR_PCT = 0.1
REACH = 1536.0          # plants this close to a building count towards the measure
DOORWAY = 192.0         # nothing grows closer than this to a door front
CAP = 768.0
STREET_HALF = 128.0
TALL = {"tree"}
LOW = {"plant", "groundcover", "rock"}
CLEARED_KINDS = TALL | LOW


def _cls(kind: str) -> str:
    return "tree" if kind in TALL else "low"


def _pct(vals: list[float], q: float) -> float:
    if not vals:
        return 0.0
    v = sorted(vals)
    return v[min(len(v) - 1, int(q * len(v)))]


def distances(p, buildings: list[dict], bases: dict, paths: list[dict], doors: list) -> dict[str, float]:
    return {"building": min((rect_dist(b, bases, *p) for b in buildings), default=1e9),
            "street": dist_to_paths(p, paths) if paths else 1e9,
            "door": min((geom.dist(p, d) for d in doors), default=1e9)}


def measure(veg: list[dict], buildings: list[dict], bases: dict, paths: list[dict], doors: list) -> dict:
    """{tree|low: {building, street, door}}: how close the source's plants come to what it built. For each
    building, door and street point, the distance to its nearest plant of the class; the clearance is the median
    over them (a feature with no plant within REACH does not count)."""
    out: dict[str, dict] = {}
    street_pts = []
    for pa in paths:
        pts = pa["points"]
        for a, b in zip(pts, pts[1:]):
            n = max(1, int(geom.dist(a, b) // 256))
            street_pts.extend((a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n) for k in range(n))
    for cls in ("tree", "low"):
        pts = [(r["pos"][0], r["pos"][1]) for r in veg if _cls(r.get("kind", "")) == cls]
        res: dict[str, float] = {}

        def nearest(d_of):
            ds = [d for d in (min((d_of(p) for p in pts), default=1e9),) if d < REACH]
            return ds[0] if ds else None
        for name, items, d_of in (
                ("building", buildings, lambda b: (lambda p: rect_dist(b, bases, *p))),
                ("door", doors, lambda d: (lambda p: geom.dist(p, d))),
                ("street", street_pts, lambda q: (lambda p: max(0.0, geom.dist(p, q) - STREET_HALF)))):
            vals = sorted(v for v in (nearest(d_of(it)) for it in items) if v is not None)
            res[name] = round(min(CAP, vals[len(vals) // 2]), 1) if vals else 0.0
        res["samples"] = len(pts)
        out[cls] = res
    return out


def apply(world: list[dict], clearance: dict, buildings: list[dict], bases: dict, paths: list[dict],
          doors: list, footprints: list[dict]) -> list[dict]:
    reach = max(max(c[k] for k in ("building", "street", "door")) for c in clearance.values()) + 2048.0
    grid: dict[tuple[int, int], list] = {}

    def cells_round(x, y, r):
        for gx in range(int((x - r) // 2048), int((x + r) // 2048) + 1):
            for gy in range(int((y - r) // 2048), int((y + r) // 2048) + 1):
                yield gx, gy
    for kind, items in (("b", buildings), ("f", footprints)):
        for it in items:
            for k in cells_round(it["pos"][0], it["pos"][1], geom.radius(it, bases)):
                grid.setdefault(k, []).append((kind, it))
    for p in paths:
        for q in p["points"]:
            grid.setdefault((int(q[0] // 2048), int(q[1] // 2048)), []).append(("p", p))
    for d in doors:
        grid.setdefault((int(d[0] // 2048), int(d[1] // 2048)), []).append(("d", d))
    rows = []
    for r in world:
        if r.get("kind") not in CLEARED_KINDS:
            continue
        p = (r["pos"][0], r["pos"][1])
        near_b, near_f, near_p, near_d = [], [], [], []
        seen = set()
        for k in cells_round(p[0], p[1], reach):
            for kind, it in grid.get(k, ()):
                if id(it) in seen:
                    continue
                seen.add(id(it))
                {"b": near_b, "f": near_f, "p": near_p, "d": near_d}[kind].append(it)
        if not seen:
            continue
        c = clearance[_cls(r["kind"])]
        d = distances(p, near_b, bases, near_p, near_d)
        why = None
        if any(rect_dist(f, bases, *p) == 0 for f in near_f):
            why = "inside a placed footprint"
        elif d["door"] < max(c["door"], DOORWAY):
            why = "doorway"
        elif d["street"] <= max(c["street"], 0.0):
            why = "street"
        elif d["building"] < c["building"]:
            why = "building"
        if why:
            rows.append({"base": r["base"], "pos": [round(v, 1) for v in r["pos"]], "by": "draft", "why": why,
                         "ref": r.get("id")})
    return sorted(rows, key=lambda x: (x["pos"][0], x["pos"][1], x["base"]))
