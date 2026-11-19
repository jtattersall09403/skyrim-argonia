"""Hist sap pools: every living Hist of a place stands in a pool of its own sap (Lore:Hatching_Pools).

A pool is King of the Murkmire's own Hist sap water: WaterPuddleHist, a placed water activator (Skyrim's puddle
outline, water/waterpuddle01.nif) whose water type is the mod's DefaultHistSapWater (amber, opaque). A placed water
is its own surface, separate from the cell's water, so it stands on any ground at any height and the worldspace's
waterline never moves. It is centred on the trunk, turned by a yaw drawn from the tree's row id, and sized to the
tree: its reach is REACH of the tree's half-width (the record's bounds, scaled), never under MIN_SCALE. It is seated
`stilts` over its own outline (the lowest of ground or water under it, DZ above), so no edge hangs in the air, and a
Hist standing in water has its sap on the water. The ground inside the outline (DISH of its half-width about its
centre) is lowered to that lowest height, a land patch of the stage's own (`by` "sap"), so the sap lies in a hollow
on a slope instead of under the ground; never raised, never across the waterline, no deeper than PATCH_MAX, and no
vertex of a cell another patch row holds. The seat stays where it is after the dig (nothing is dug below it).

A living Hist is a row whose base's editor id is a Hist tree, trunk or gland (King of the Murkmire's HistTree*,
HistTrunk*, HistGland*) and not dead (*Dead*: a dead Hist's pool is dry). Roots are not a Hist.

    python -m tools.places.draft.sap <place_id>      the dry run: what the `sap` stage would add, nothing written
"""
from __future__ import annotations

import argparse
import hashlib
import math
import re
import sys

POOL = "King of the Murkmire.esp:3D870E"   # WaterPuddleHist: waterpuddle01.nif with DefaultHistSapWater
POOL_HALF = 175.0                           # units: the puddle's half-width at scale 1 (bounds -154..148, -152..199)
POOL_CENTRE = (-3.1, 23.5)                  # the puddle's centre in its own frame
BOX = (-154.4, -152.6, 148.2, 199.5)        # the puddle's outline box at scale 1 (x0, y0, x1, y1)
FOOT = 0.6                                  # the share of the box, about its centre, the seat reads the ground over
REACH = 0.9                                 # the pool reaches this much of the tree's half-width
MIN_SCALE = 2.2                             # a young Hist's pool still reaches past its roots
TOL = 64.0                                  # units: a pool this far off its trunk's centre is off its tree
DZ = 3.0                                    # units of sap over the hollow's floor
DISH = 0.75                                 # the share of the pool's half-width the hollow reaches
PATCH_MAX = 105.0                           # units: the most the hollow lowers any point (the draft's land bound)
LIVING = re.compile(r"^Hist(Tree|Trunk|Gland)\d+[A-Za-z]*$")


def living(base: dict | None) -> bool:
    e = str((base or {}).get("edid") or "")
    return bool(LIVING.match(e)) and "dead" not in e.lower() and "roots" not in e.lower()


def half_width(base: dict, scale: float) -> float:
    b = base.get("bounds") or [[-200, -200, 0], [200, 200, 0]]
    return scale * (max(abs(b[0][0]), abs(b[1][0])) + max(abs(b[0][1]), abs(b[1][1]))) / 2


def turned(u: float, v: float, rz: float) -> tuple[float, float]:
    """A point of the pool's own frame turned by its yaw (Skyrim's yaw turns clockwise seen from above)."""
    c, s = math.cos(rz), math.sin(rz)
    return u * c + v * s, -u * s + v * c


def pool_for(place_id: str, t: dict, base: dict) -> dict:
    """The sap pool row of one Hist row. Its seat's footprint is the inner part of its outline (FOOT of the box
    about its centre), scaled, so the lowest ground is read where the sap lies, not past the outline's corners."""
    s = round(max(MIN_SCALE, REACH * half_width(base, float(t.get("scale", 1.0))) / POOL_HALF), 2)
    rz = round(int(hashlib.sha256(f"{t['id']}/sap".encode()).hexdigest()[:8], 16) / 0xFFFFFFFF * 2 * math.pi, 5)
    dx, dy = turned(POOL_CENTRE[0] * s, POOL_CENTRE[1] * s, rz)
    foot = [round((c + (b - c) * FOOT) * s, 1) for b, c in zip(BOX, POOL_CENTRE * 2)]
    return {"id": f"{place_id}.sap.{t['id'].split('.', 1)[-1]}", "base": POOL, "kind": "activator",
            "pos": [round(t["pos"][0] - dx, 2), round(t["pos"][1] - dy, 2), t["pos"][2]], "rot": [0.0, 0.0, rz],
            "scale": s, "layer": "place", "flags": [], "src": None, "seat": {"mode": "stilts", "dz": DZ, "foot": foot},
            "why": f"the sap pool at the roots of {base.get('edid')} (Lore:Hatching_Pools): King of the Murkmire's "
                   f"WaterPuddleHist, its Hist sap water"}


def centre(p: dict) -> tuple[float, float]:
    """A pool row's centre on the ground (its outline's middle, turned and scaled)."""
    s, rz = float(p.get("scale", 1.0)), float((p.get("rot") or [0, 0, 0])[2])
    dx, dy = turned(POOL_CENTRE[0] * s, POOL_CENTRE[1] * s, rz)
    return p["pos"][0] + dx, p["pos"][1] + dy


def plan(place_id: str, ext: list[dict], bases: dict) -> list[dict]:
    """A pool for every living Hist row of a place's exterior, in row id order; a Hist already standing in a pool
    placed by hand (`draft.add`, the studio) keeps that one."""
    own = [r for r in ext if r.get("base") == POOL and ".sap." not in r["id"]]
    return [pool_for(place_id, t, bases[t["base"]]) for t in sorted(pooled(ext, bases), key=lambda r: r["id"])
            if not any(math.dist(centre(p), t["pos"][:2]) <= TOL for p in own)]


def pooled(ext: list[dict], bases: dict) -> list[dict]:
    """The living Hists that stand in a pool of their own: every Hist tree and trunk, and a gland only where it grows
    apart from them (a gland within a tree's pool is a growth of that tree, and its sap is the tree's pool)."""
    hists = [t for t in ext if living(bases.get(t["base"])) and t.get("kind") != "door"]
    trees = [t for t in hists if "Gland" not in str(bases[t["base"]].get("edid"))]
    reach = [(t, POOL_HALF * pool_for("", t, bases[t["base"]])["scale"]) for t in trees]
    return trees + [g for g in hists if g not in trees
                    and not any(math.dist(g["pos"][:2], t["pos"][:2]) <= r for t, r in reach)]


def faults(ext: list[dict], bases: dict) -> list[str]:
    """A living Hist without a sap pool centred on its trunk (within TOL), and a stage pool whose Hist is gone."""
    pools = [r for r in ext if r.get("base") == POOL]
    out = []
    hists = [t for t in ext if living(bases.get(t["base"]))]
    for t in pooled(ext, bases):
        if not any(math.dist(centre(p), t["pos"][:2]) <= TOL for p in pools):
            out.append(f"{t['id']}: a Hist without its sap pool")
    ids = {t["id"].split(".", 1)[-1] for t in hists}
    for p in pools:
        if ".sap." in p["id"] and p["id"].split(".sap.", 1)[1] not in ids:
            out.append(f"{p['id']}: its Hist is gone")
    return out


def dish(G, ext: list[dict], bases: dict, taken: set) -> list[dict]:
    """Land rows (`by` "sap") that lower the ground inside every pool centred on a living Hist to the pool's seat
    height (its lowest ground or water); cells in `taken` (another row's) are left alone."""
    from tools.places.draft.fit import WATERLINE_GAP
    from tools.places.seat import STEP, reference_z
    hists = [t for t in ext if living(bases.get(t["base"]))]
    cells: dict[tuple, dict] = {}
    for p in sorted(ext, key=lambda r: r["id"]):
        if p.get("base") != POOL or not any(math.dist(centre(p), t["pos"][:2]) <= TOL for t in hists):
            continue
        sd = p.get("seat") or {}
        floor = reference_z(G, "stilts", p["pos"][0], p["pos"][1], float(p["rot"][2]), sd.get("foot"))
        if floor is None:
            continue
        rad = DISH * POOL_HALF * float(p.get("scale", 1.0))   # a round hollow, eased out over one vertex past it
        cx, cy = centre(p)
        # the floor is the lowest point any seat sample could read (every vertex up to two past the hollow), so the
        # pool seated again on the dug ground sits on the floor and a second dig changes nothing
        for gx in range(math.floor((cx - rad) / STEP) - 2, math.ceil((cx + rad) / STEP) + 3):
            for gy in range(math.floor((cy - rad) / STEP) - 2, math.ceil((cy + rad) / STEP) + 3):
                h = G.vertex(gx, gy)
                if h is not None and math.dist((gx * STEP, gy * STEP), (cx, cy)) <= rad + 2 * STEP:
                    w = G.water(gx * STEP, gy * STEP)
                    floor = min(floor, max(h, w) if w is not None else h)
        for gx in range(math.floor((cx - rad) / STEP) - 1, math.ceil((cx + rad) / STEP) + 2):
            for gy in range(math.floor((cy - rad) / STEP) - 1, math.ceil((cy + rad) / STEP) + 2):
                d = math.dist((gx * STEP, gy * STEP), (cx, cy))
                blend = 1.0 if d <= rad else max(0.0, 1 - (d - rad) / STEP)
                h = G.vertex(gx, gy)
                if h is None or blend <= 0 or h <= floor:
                    continue
                dz = max(-PATCH_MAX, (floor - h) * blend)
                w = G.water(gx * STEP, gy * STEP)
                if w is not None and h >= w:
                    dz = max(dz, min(0.0, w + WATERLINE_GAP - h))   # dry land stays dry
                dz = round(dz, 1)
                if dz > -1:
                    continue
                for (kx, col), (ky, row) in ((divmod(gx, 32), divmod(gy, 32)),):
                    edges = [((kx, ky), row, col)] + ([((kx - 1, ky), row, 32)] if col == 0 else []) \
                        + ([((kx, ky - 1), 32, col)] if row == 0 else []) + ([((kx - 1, ky - 1), 32, 32)] if col == 0 and row == 0 else [])
                    for cell, r_, c_ in edges:
                        if cell in taken:
                            continue
                        c = cells.setdefault(cell, {})
                        c[(r_, c_)] = min(c.get((r_, c_), 0.0), dz)
    return [{"cell": list(k), "verts": [[r, c, v] for (r, c), v in sorted(vs.items())],
             "why": "the hollow of a Hist's sap pool", "by": "sap"} for k, vs in sorted(cells.items()) if vs]


def apply(st, log=print) -> None:
    """The `sap` stage: the place's sap pools made again from its standing Hist trees, and their hollows; place.json's
    `sap` lists the pools. A pool row the owner's studio save touched is the owner's (the stage runner keeps it)."""
    from tools.places.seat import Ground, seat_all
    rows, bases = want(st)
    old = {a["id"] for a in (st.place.get("sap") or {}).get("added") or []}
    keep = {r["id"] for r in rows}
    st.ext[:] = [r for r in st.ext if r["id"] not in old or r["id"] in keep]
    have = {r["id"]: r for r in st.ext}
    for r in rows:
        if r["id"] in have:
            have[r["id"]].update({k: r[k] for k in ("base", "pos", "rot", "scale", "seat", "why")})
        else:
            st.ext.append(r)
    other = [r for r in st.files["land"] if r.get("by") != "sap"]
    G = Ground.load(st.grd.path)
    G.apply_patches(other)
    pools = [r for r in st.ext if r.get("base") == POOL]
    seat_all(pools, G)
    hollow = dish(G, st.ext, {**st.bases, **bases}, {tuple(r["cell"]) for r in other})
    st.files["land"][:] = other + hollow
    G.apply_patches(hollow)
    st.G = G
    near = [r for r in st.ext if any(math.dist(r["pos"][:2], centre(p)) <= DISH * POOL_HALF * float(p.get("scale", 1.0)) + 600
                                     for p in pools)]
    seat_all(near, G)                       # what stands over a hollow follows the ground down
    st.place["sap"] = {"added": [{"id": r["id"], "on": r["id"].split(".sap.", 1)[1]} for r in rows]}
    if POOL in bases:
        st.bases[POOL] = bases[POOL]
    log(f"draft sap {st.place_id}: {len(rows)} sap pools, hollows in {len(hollow)} cells")


def want(st) -> tuple[list[dict], dict]:
    return rows_for(st.place_id, st.ext, st.bases)


def rows_for(place_id: str, ext: list[dict], bases: dict) -> tuple[list[dict], dict]:
    """Pool rows for a place's exterior rows, and the bases with the pool's (none when the catalogue lacks it)."""
    from tools.places.draft.io import catalogue_bases
    bases = dict(bases)
    bases.update(catalogue_bases({POOL} - set(bases)))
    if POOL not in bases:
        return [], bases
    return plan(place_id, ext, bases), bases


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("place_id")
    a = ap.parse_args(argv)
    from tools.places.draft.stages import Standing
    rows, _ = want(Standing(a.place_id))
    print(f"sap {a.place_id} (dry run): {len(rows)} pools")
    for r in rows:
        print(f"  {r['id']} at {r['pos'][:2]} scale {r['scale']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
