"""Hist sap pools: every living Hist of a place has a still pool of its own amber sap at its roots (Lore:Hatching_Pools).

A pool is our own placed water, ArgoniaHistSapPool (tools/places/own_bases.py): vanilla's round puddle outline
(water/waterpuddle01.nif) carrying our water type ArgoniaHistSapWater, a copy of the Eastmarch hot-spring water
recoloured amber, part clear at the rim and dark in the deep. A placed water is its own surface, separate from the
cell's water, so it stands at any height and the worldspace's waterline never moves. It is turned by a yaw drawn from
the tree's row id and sized to the tree: its reach is REACH of the tree's half-width (the record's bounds, scaled),
never under MIN_SCALE.

The pool lies in a BOWL the stage digs (land rows of its own, `by` "sap"), so the water has depth to shade:
- the rim is the lowest ground anywhere under the pool's outline (and round the bowl), so no edge of the surface
  hangs in the air; the surface is LIP under the rim (the pool's z, set here: its seat is `free`);
- inside the bowl's radius (DISH of the pool's half-width) the floor falls on a cosine from the rim to DEPTH under
  the surface at the middle, level at the rim and at the middle, so the bank is a slope, never a step;
- round it, over BANK, ground higher than the rim eases down to it (a pool on a slope sits in a cut, not a step);
- the dig only lowers, never more than PATCH_MAX, never a vertex of a cell another land row holds, and never dry land
  to within WATERLINE_GAP of the cell's water: the floor stays above our water, so the bowl is shallower near it.

Where it lies: centred on the trunk when the ground under the whole outline is dry. A Hist standing in our water does
not get sap laid on the water: its pool goes on the nearest dry bank at its foot (BANK_REACH past the tree's
half-width, sixteen bearings, nearest first; the ground there dry under the whole outline, no building, furniture or
door within the bowl, and level enough that the dig stays within PATCH_MAX). With no such bank the Hist gets no pool
and the stage says so: place.json `sap.none` lists it, with why, and the draft's plan says how the place shows its
Hist's sap.

A living Hist is a row whose base's editor id is a Hist tree, trunk or gland (King of the Murkmire's HistTree*,
HistTrunk*, HistGland*) and not dead (*Dead*: a dead Hist's pool is dry). Roots are not a Hist. A pool placed by hand
(ours, or King of the Murkmire's WaterPuddleHist) centred on a trunk is that tree's own; the stage keeps it.

    python -m tools.places.draft.sap <place_id>      the dry run: what the `sap` stage would add, nothing written
"""
from __future__ import annotations

import argparse
import hashlib
import math
import re
import sys

from tools.places.own_bases import SAP_POOL

POOL = SAP_POOL                             # ArgoniaHistSapPool: waterpuddle01.nif with ArgoniaHistSapWater
OLD_POOL = "King of the Murkmire.esp:3D870E"  # WaterPuddleHist, the mod's own: a hand-placed one is still a pool
POOLS = (POOL, OLD_POOL)
POOL_HALF = 175.0                           # units: the puddle's half-width at scale 1 (bounds -154..148, -152..199)
POOL_CENTRE = (-3.1, 23.5)                  # the puddle's centre in its own frame
BOX = (-154.4, -152.6, 148.2, 199.5)        # the puddle's outline box at scale 1 (x0, y0, x1, y1)
REACH = 0.9                                 # the pool reaches this much of the tree's half-width
MIN_SCALE = 2.2                             # a young Hist's pool still reaches past its roots
TOL = 64.0                                  # units: a hand pool this far off its trunk's centre is off its tree
DISH = 0.75                                 # the bowl's radius, a share of the pool's half-width
DEPTH = 64.0                                # units of sap at the bowl's middle (vanilla's still pools: ankle to knee)
MIN_DEPTH = 24.0                            # a bank site shallower than this is passed over for a deeper one
LIP = 4.0                                   # units the surface lies under the rim
BANK = 128.0                                # units outside the bowl over which higher ground eases down to the rim
BANK_REACH = 600.0                          # units past the tree's half-width a bank pool may lie
PATCH_MAX = 105.0                           # units: the most the dig lowers any point (the draft's land bound)
BLOCKS = ("building", "furniture", "door", "container", "actor")   # kinds a bank bowl is never dug under
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


def scale_of(t: dict, base: dict) -> float:
    return round(max(MIN_SCALE, REACH * half_width(base, float(t.get("scale", 1.0))) / POOL_HALF), 2)


def yaw_of(t: dict) -> float:
    return round(int(hashlib.sha256(f"{t['id']}/sap".encode()).hexdigest()[:8], 16) / 0xFFFFFFFF * 2 * math.pi, 5)


def pool_for(place_id: str, t: dict, base: dict, at: tuple[float, float] | None = None) -> dict:
    """The sap pool row of one Hist row, its outline's centre at `at` (the trunk when None). Its z is the stage's
    (`dish` sets it to the surface over the bowl)."""
    s, rz = scale_of(t, base), yaw_of(t)
    cx, cy = at or (t["pos"][0], t["pos"][1])
    dx, dy = turned(POOL_CENTRE[0] * s, POOL_CENTRE[1] * s, rz)
    where = "at its roots" if at is None else "on the bank at its foot (the tree stands in water)"
    return {"id": f"{place_id}.sap.{t['id'].split('.', 1)[-1]}", "base": POOL, "kind": "activator",
            "pos": [round(cx - dx, 2), round(cy - dy, 2), t["pos"][2]], "rot": [0.0, 0.0, rz],
            "scale": s, "layer": "place", "flags": [], "src": None, "seat": {"mode": "free"},
            "why": f"the sap pool of {base.get('edid')} {where} (Lore:Hatching_Pools): our ArgoniaHistSapPool, "
                   f"amber Hist sap in a bowl"}


def centre(p: dict) -> tuple[float, float]:
    """A pool row's centre on the ground (its outline's middle, turned and scaled)."""
    s, rz = float(p.get("scale", 1.0)), float((p.get("rot") or [0, 0, 0])[2])
    dx, dy = turned(POOL_CENTRE[0] * s, POOL_CENTRE[1] * s, rz)
    return p["pos"][0] + dx, p["pos"][1] + dy


def outline(cx: float, cy: float, s: float, rz: float, n: int = 7) -> list[tuple[float, float]]:
    """Points over the pool's whole outline box (n x n), centred at (cx, cy)."""
    out = []
    for i in range(n):
        for j in range(n):
            u = BOX[0] + (BOX[2] - BOX[0]) * i / (n - 1) - POOL_CENTRE[0]
            v = BOX[1] + (BOX[3] - BOX[1]) * j / (n - 1) - POOL_CENTRE[1]
            du, dv = turned(u * s, v * s, rz)
            out.append((cx + du, cy + dv))
    return out


def ring(cx: float, cy: float, r: float, n: int = 24) -> list[tuple[float, float]]:
    return [(cx + r * math.cos(2 * math.pi * k / n), cy + r * math.sin(2 * math.pi * k / n)) for k in range(n)]


def bowl(G, cx: float, cy: float, s: float, rz: float) -> dict | None:
    """The bowl a pool of scale s centred at (cx, cy) would lie in: its rim (lowest ground under the outline and round
    the bowl), the depth the water allows, the highest ground the dig must cut, and whether any of it is wet (ground
    under the outline lower than WATERLINE_GAP over the cell's water). None where the ground is missing."""
    from tools.places.draft.fit import WATERLINE_GAP
    r = DISH * POOL_HALF * s
    pts = outline(cx, cy, s, rz) + ring(cx, cy, r) + ring(cx, cy, r * 0.5, 12) + [(cx, cy)]
    hs, wmax, wet = [], None, False
    for x, y in pts:
        h = G.height(x, y)
        if h is None:
            return None
        w = G.water(x, y)
        if w is not None:
            wet |= h < w + WATERLINE_GAP
            wmax = w if wmax is None else max(wmax, w)
        hs.append(h)
    rim = min(hs)
    depth = DEPTH if wmax is None else max(0.0, min(DEPTH, rim - LIP - wmax - WATERLINE_GAP))
    high = max([h for h in (G.height(x, y) for x, y in ring(cx, cy, r + BANK) + ring(cx, cy, r, 12)) if h is not None] + hs)
    return {"rim": rim, "depth": depth, "high": high, "wet": wet, "r": r}


def site(G, t: dict, base: dict, ext: list[dict], bases: dict) -> tuple[float, float] | None:
    """Where a Hist's pool lies: the trunk when the ground under its outline is dry; else the nearest dry, open, level
    enough bank at its foot; None when there is none."""
    s, rz = scale_of(t, base), yaw_of(t)
    tx, ty = t["pos"][0], t["pos"][1]
    b = bowl(G, tx, ty, s, rz)
    if b is None or not b["wet"]:
        return None if b is None else (tx, ty)
    r = DISH * POOL_HALF * s
    blocks = [q for q in ext if q.get("kind") in BLOCKS or (q.get("kind") == "static" and "house" in str((bases.get(q["base"]) or {}).get("edid", "")).lower())]
    far = half_width(base, float(t.get("scale", 1.0))) + BANK_REACH
    best = None
    d = r * 0.5
    while d <= far and best is None:
        for k in range(16):
            cx, cy = tx + d * math.sin(2 * math.pi * k / 16), ty + d * math.cos(2 * math.pi * k / 16)
            b = bowl(G, cx, cy, s, rz)
            if b is None or b["wet"] or b["depth"] < MIN_DEPTH or b["high"] - (b["rim"] - LIP - b["depth"]) > PATCH_MAX:
                continue
            if any(math.dist(q["pos"][:2], (cx, cy)) <= r + 64 for q in blocks):
                continue
            best = (round(cx, 2), round(cy, 2))
            break
        d += 64.0
    return best


def plan(place_id: str, ext: list[dict], bases: dict, G=None, none: list | None = None) -> list[dict]:
    """A pool for every living Hist row of a place's exterior, in row id order; a Hist already standing in a pool
    placed by hand (`draft.add`, the studio) keeps that one. With the ground `G`, each pool's site is chosen (`site`);
    a Hist that has none is added to `none` ({"on", "why"})."""
    own = [r for r in ext if r.get("base") in POOLS and ".sap." not in r["id"]]
    out = []
    for t in sorted(pooled(ext, bases), key=lambda r: r["id"]):
        if any(math.dist(centre(p), t["pos"][:2]) <= TOL for p in own):
            continue
        at = None
        if G is not None:
            at = site(G, t, bases[t["base"]], ext, bases)
            if at is None:
                if none is not None:
                    none.append({"on": t["id"], "why": "the tree stands in water with no dry bank at its foot"})
                continue
            if at == (t["pos"][0], t["pos"][1]):
                at = None
        out.append(pool_for(place_id, t, bases[t["base"]], at))
    return out


def pooled(ext: list[dict], bases: dict) -> list[dict]:
    """The living Hists that stand in a pool of their own: every Hist tree and trunk, and a gland only where it grows
    apart from them (a gland within a tree's pool is a growth of that tree, and its sap is the tree's pool)."""
    hists = [t for t in ext if living(bases.get(t["base"])) and t.get("kind") != "door"]
    trees = [t for t in hists if "Gland" not in str(bases[t["base"]].get("edid"))]
    reach = [(t, POOL_HALF * scale_of(t, bases[t["base"]])) for t in trees]
    return trees + [g for g in hists if g not in trees
                    and not any(math.dist(g["pos"][:2], t["pos"][:2]) <= r for t, r in reach)]


def owner_of(p: dict, hists: list[dict]) -> dict | None:
    """The Hist a pool row belongs to: the stage's by its id (`<place>.sap.<rest of the Hist's id>`), a hand pool by
    standing centred on the trunk."""
    if ".sap." in p["id"]:
        rest = p["id"].split(".sap.", 1)[1]
        return next((t for t in hists if t["id"].split(".", 1)[-1] == rest), None)
    return next((t for t in hists if math.dist(centre(p), t["pos"][:2]) <= TOL), None)


def faults(ext: list[dict], bases: dict, none=()) -> list[str]:
    """A living Hist without its sap pool (unless place.json `sap.none` lists it), and a stage pool whose Hist is
    gone."""
    pools = [r for r in ext if r.get("base") in POOLS]
    hists = [t for t in ext if living(bases.get(t["base"]))]
    skip = {n.get("on") if isinstance(n, dict) else n for n in none or ()}
    out = []
    owned = {id(owner_of(p, hists)) for p in pools}
    for t in pooled(ext, bases):
        if id(t) not in owned and t["id"] not in skip:
            out.append(f"{t['id']}: a Hist without its sap pool")
    for p in pools:
        if ".sap." in p["id"] and owner_of(p, hists) is None:
            out.append(f"{p['id']}: its Hist is gone")
    return out


def dish(G, ext: list[dict], bases: dict, taken: set) -> list[dict]:
    """Land rows (`by` "sap") that dig the bowl of every pool that belongs to a living Hist (`bowl`, the module's
    shape), on the ground as it stands without the stage's own rows; cells in `taken` (another row's) are left alone.
    Each stage pool's z is set to its surface, LIP under the rim; a hand pool keeps the z it was given."""
    from tools.places.draft.fit import WATERLINE_GAP
    from tools.places.seat import STEP
    hists = [t for t in ext if living(bases.get(t["base"]))]
    cells: dict[tuple, dict] = {}
    for p in sorted(ext, key=lambda r: r["id"]):
        if p.get("base") not in POOLS or owner_of(p, hists) is None:
            continue
        s, rz = float(p.get("scale", 1.0)), float(p["rot"][2])
        cx, cy = centre(p)
        b = bowl(G, cx, cy, s, rz)
        if b is None:
            continue
        rim, r = b["rim"], b["r"]
        if ".sap." in p["id"]:
            p["pos"][2] = round(rim - LIP, 1)
        drop = LIP + b["depth"]
        reach = r + BANK
        for gx in range(math.floor((cx - reach) / STEP), math.ceil((cx + reach) / STEP) + 1):
            for gy in range(math.floor((cy - reach) / STEP), math.ceil((cy + reach) / STEP) + 1):
                d = math.dist((gx * STEP, gy * STEP), (cx, cy))
                h = G.vertex(gx, gy)
                if h is None or d > reach:
                    continue
                if d <= r:
                    target = rim - drop * (1 + math.cos(math.pi * d / r)) / 2
                else:
                    e = (d - r) / BANK
                    target = rim + (h - rim) * e * e * (3 - 2 * e)
                if target >= h:
                    continue
                dz = max(-PATCH_MAX, target - h)
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
             "why": "the bowl of a Hist's sap pool", "by": "sap"} for k, vs in sorted(cells.items()) if vs]


def apply(st, log=print) -> None:
    """The `sap` stage: the place's sap pools made again from its standing Hist trees, and their bowls; place.json's
    `sap` lists the pools (`added`) and the Hists that have none (`none`). A pool row the owner's studio save touched is
    the owner's (the stage runner keeps it)."""
    from tools.places.seat import Ground, seat_all
    other = [r for r in st.files["land"] if r.get("by") != "sap"]
    G = Ground.load(st.grd.path)
    G.apply_patches(other)
    none: list[dict] = []
    rows, bases = rows_for(st.place_id, st.ext, st.bases, G, none)
    old = {a["id"] for a in (st.place.get("sap") or {}).get("added") or []}
    keep = {r["id"] for r in rows}
    st.ext[:] = [r for r in st.ext if r["id"] not in old or r["id"] in keep]
    have = {r["id"]: r for r in st.ext}
    for r in rows:
        if r["id"] in have:
            have[r["id"]].update({k: r[k] for k in ("base", "pos", "rot", "scale", "seat", "why")})
        else:
            st.ext.append(r)
    hollow = dish(G, st.ext, {**st.bases, **bases}, set())   # the place's own rows add (build.plan_land): its ground's cells are dug too
    st.files["land"][:] = other + hollow
    G.apply_patches(hollow)
    st.G = G
    pools = [r for r in st.ext if r.get("base") in POOLS]
    near = [r for r in st.ext if r.get("base") not in POOLS and any(
        math.dist(r["pos"][:2], centre(p)) <= DISH * POOL_HALF * float(p.get("scale", 1.0)) + BANK + 600 for p in pools)]
    seat_all(near, G)                       # what stands over a bowl follows the ground down
    st.place["sap"] = {"added": [{"id": r["id"], "on": r["id"].split(".sap.", 1)[1]} for r in rows]}
    if none:
        st.place["sap"]["none"] = none
    if POOL in bases:
        st.bases[POOL] = bases[POOL]
    log(f"draft sap {st.place_id}: {len(rows)} sap pools, bowls in {len(hollow)} cells"
        + "".join(f"; no pool for {n['on']}: {n['why']}" for n in none))


def rows_for(place_id: str, ext: list[dict], bases: dict, G=None, none: list | None = None) -> tuple[list[dict], dict]:
    """Pool rows for a place's exterior rows, and the bases with the pool's (none when the catalogue lacks it)."""
    from tools.places.draft.io import catalogue_bases
    bases = dict(bases)
    bases.update(catalogue_bases({POOL} - set(bases)))
    if POOL not in bases:
        return [], bases
    return plan(place_id, ext, bases, G, none), bases


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("place_id")
    a = ap.parse_args(argv)
    from tools.places.draft.stages import Standing
    from tools.places.seat import Ground
    st = Standing(a.place_id)
    G = Ground.load(st.grd.path)
    G.apply_patches([r for r in st.files["land"] if r.get("by") != "sap"])
    none: list[dict] = []
    rows, _ = rows_for(a.place_id, st.ext, st.bases, G, none)
    print(f"sap {a.place_id} (dry run): {len(rows)} pools")
    for r in rows:
        print(f"  {r['id']} at {r['pos'][:2]} scale {r['scale']}")
    for n in none:
        print(f"  no pool for {n['on']}: {n['why']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
