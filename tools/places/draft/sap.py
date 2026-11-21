"""Hist sap pools: every living Hist of a place stands in a pool of its own sap (Lore:Hatching_Pools).

A pool is King of the Murkmire's own Hist sap water: WaterPuddleHist, a placed water activator (Skyrim's puddle
outline, water/waterpuddle01.nif) whose water type is the mod's DefaultHistSapWater (amber, opaque). A placed water
is its own surface, separate from the cell's water, so it stands on any ground at any height and the worldspace's
waterline never moves. It is turned by a yaw drawn from the tree's row id and sized by the TRUNK at the ground, never
the crown: its reach is the trunk's radius at its foot (TRUNK_R per Hist base, measured from the mesh at ground
height; else TRUNK_SHARE of the record's half-width), scaled, plus SAP_BAND of open sap, never under MIN_SCALE. It
lies on the trunk's centre, or off it by an offset (`draft.sap.offset` of place.json: [dx, dy], or {hist id: [dx,
dy]}; with `draft.sap.scale`, a number or {hist id: number}, the pool's own scale: a pool placed BY HAND, wherever
the hand put it, even off the trunk, never moved or resized by the stage's scoring, and logged as hand-placed; it is
the Hist's pool by its id), else one the stage chooses, the trunk kept inside the sap: each side (and the pool shrunk to SHRINK of its
size) is scored by the bank the dig would leave over the sap plus COVER_W times the share of the sap hidden from the
sky (a deck, walkway, bridge or platform over it, or the trunk's own foot), and the lowest wins, so a pool is never
put under the ring's platform when a side a person can look onto exists; without a bank the pool stays centred
unless a side uncovers a tenth more of it. Its surface is seated `stilts` over its whole outline, rim and all (the lowest of ground or water under it, DZ
above), so a person at the rim looks down onto sap, never up over a lip. The stage's hollow (a land patch, `by`
"sap") lowers the ground inside the outline to under the surface, and the rim one vertex round it to the surface
(RIM_LIP over it), so the rim is level all round; never raised, never across the waterline, no vertex lowered more
than PATCH_MAX and no vertex of a cell another patch row holds (the carried ground's rows excepted: the hollow is
dug on top of them, and the build adds a vertex's changes); every other row seated on the ground keeps its height on the
dug ground (`hold_others`: its seat's dz pinned), so the dig never moves another row. The surface is the lowest rim (DZ over the lowest ground):
the sap never stands above its own rim. Where the ground falls more than PATCH_MAX across the pool, the stage moves
or shrinks the pool to the side with the least bank; what bank remains is ground standing out of the sap on its high
side, and the stage says so (`banks`). The seat stays where it is after the dig (nothing is dug below it).

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
TRUNK_R = {"HistTree01": 120.0}             # units at scale 1: the trunk's radius at the ground, measured from the mesh
TRUNK_SHARE = 0.15                          # else this share of the record's half-width is the trunk at the ground
SAP_BAND = 200.0                            # units of open sap round the trunk's foot
MIN_SCALE = 1.6                             # a young Hist's pool still reaches past its roots
RIM_LIP = 2.0                               # units: the dug rim stands this far over the surface
OPEN = 0.1                                  # an offset is chosen only when it opens this share more of the pool
COVER = re.compile(r"platform|deck|walkway|bridge|dock|pier|boardwalk|scaffold", re.I)
DZ = 3.0                                    # units of sap over the hollow's floor
SEAT_REACH = max(abs(v) for v in BOX) / POOL_HALF   # the share of the pool's half-width its seat reads the ground over
DISH = 0.85                                 # the share of the pool's half-width its sap covers (the puddle's outline)
PATCH_MAX = 105.0                           # units: the most the hollow lowers any point (the draft's land bound)
COVER_W = 400.0                             # a wholly hidden pool scores as a bank of this many units
SHRINK = (1.0, 0.85, 0.7)                   # the sizes tried, as shares of the pool's reach (never under MIN_REACH)
MIN_BAND = 80.0                             # units of sap a shrunk pool keeps round the trunk's foot
LIVING = re.compile(r"^Hist(Tree|Trunk|Gland)\d+[A-Za-z]*$")


def living(base: dict | None) -> bool:
    e = str((base or {}).get("edid") or "")
    return bool(LIVING.match(e)) and "dead" not in e.lower() and "roots" not in e.lower()


def half_width(base: dict, scale: float) -> float:
    b = base.get("bounds") or [[-200, -200, 0], [200, 200, 0]]
    return scale * (max(abs(b[0][0]), abs(b[1][0])) + max(abs(b[0][1]), abs(b[1][1]))) / 2


def trunk_r(base: dict, scale: float) -> float:
    """The trunk's radius at the ground, scaled (TRUNK_R by base, else TRUNK_SHARE of the half-width)."""
    r = TRUNK_R.get(str(base.get("edid") or ""))
    return scale * r if r is not None else TRUNK_SHARE * half_width(base, scale)


def reach(base: dict, scale: float) -> float:
    return max(MIN_SCALE * POOL_HALF, trunk_r(base, scale) + SAP_BAND)


def turned(u: float, v: float, rz: float) -> tuple[float, float]:
    """A point of the pool's own frame turned by its yaw (Skyrim's yaw turns clockwise seen from above)."""
    c, s = math.cos(rz), math.sin(rz)
    return u * c + v * s, -u * s + v * c


def pool_for(place_id: str, t: dict, base: dict, off=(0.0, 0.0), k: float = 1.0, scale: float | None = None) -> dict:
    """The sap pool row of one Hist row, its centre `off` the trunk's. Its seat's footprint is its whole outline box,
    scaled, so the surface is read from the lowest ground of the rim as well as inside it."""
    s = round(scale if scale is not None else k * reach(base, float(t.get("scale", 1.0))) / POOL_HALF, 2)
    rz = round(int(hashlib.sha256(f"{t['id']}/sap".encode()).hexdigest()[:8], 16) / 0xFFFFFFFF * 2 * math.pi, 5)
    dx, dy = turned(POOL_CENTRE[0] * s, POOL_CENTRE[1] * s, rz)
    foot = [round(b * s, 1) for b in BOX]
    return {"id": f"{place_id}.sap.{t['id'].split('.', 1)[-1]}", "base": POOL, "kind": "activator",
            "pos": [round(t["pos"][0] + off[0] - dx, 2), round(t["pos"][1] + off[1] - dy, 2), t["pos"][2]], "rot": [0.0, 0.0, rz],
            "scale": s, "layer": "place", "flags": [], "src": None, "seat": {"mode": "stilts", "dz": DZ, "foot": foot},
            "why": f"the sap pool at the roots of {base.get('edid')} (Lore:Hatching_Pools): King of the Murkmire's "
                   f"WaterPuddleHist, its Hist sap water"}


def centre(p: dict) -> tuple[float, float]:
    """A pool row's centre on the ground (its outline's middle, turned and scaled)."""
    s, rz = float(p.get("scale", 1.0)), float((p.get("rot") or [0, 0, 0])[2])
    dx, dy = turned(POOL_CENTRE[0] * s, POOL_CENTRE[1] * s, rz)
    return p["pos"][0] + dx, p["pos"][1] + dy


def of_hist(p: dict, t: dict) -> bool:
    """A pool is a Hist's own: it holds the trunk, or it is the pool the stage set for that Hist (its id is the
    Hist's with `.sap.` after the place), wherever a hand put it."""
    return holds(p, t) or str(p.get("id", "")).endswith(".sap." + str(t.get("id", "")).split(".", 1)[-1])


def holds(p: dict, t: dict) -> bool:
    """A pool holds a Hist when the trunk's centre lies inside its sap (within its reach of the pool's centre)."""
    return math.dist(centre(p), t["pos"][:2]) <= POOL_HALF * float(p.get("scale", 1.0))


def covers(ext: list[dict], bases: dict) -> list[tuple]:
    """The plan boxes (x0, y0, x1, y1) of every deck, walkway, platform or bridge row: what hides sap from the sky."""
    out = []
    for r in ext:
        b = bases.get(r.get("base")) or {}
        if not COVER.search(str(b.get("edid") or "")) or not b.get("bounds"):
            continue
        (x0, y0, _), (x1, y1, _) = b["bounds"]
        s, rz = float(r.get("scale", 1.0)), float((r.get("rot") or [0, 0, 0])[2])
        pts = [turned(u * s, v * s, rz) for u in (x0, x1) for v in (y0, y1)]
        xs, ys = [r["pos"][0] + p[0] for p in pts], [r["pos"][1] + p[1] for p in pts]
        out.append((min(xs), min(ys), max(xs), max(ys)))
    return out


def open_share(cx: float, cy: float, rad: float, boxes: list[tuple], trunk=None) -> float:
    """The share of a round pool's points (rings at 0.2..1.0 of rad, 16 to a ring, and the centre) under no box and
    outside the trunk's foot (trunk: (x, y, r)), the sap a person can see."""
    pts = [(cx, cy)] + [(cx + rad * k / 5 * math.cos(a * math.pi / 8), cy + rad * k / 5 * math.sin(a * math.pi / 8))
                        for k in range(1, 6) for a in range(16)]
    def seen(x, y):
        return not any(x0 <= x <= x1 and y0 <= y <= y1 for x0, y0, x1, y1 in boxes) \
            and not (trunk and math.dist((x, y), trunk[:2]) <= trunk[2])
    return sum(seen(x, y) for x, y in pts) / len(pts)


def relief(G, cx: float, cy: float, rad: float) -> float:
    """How far the ground falls across a round pool's outline (its highest minus its lowest vertex within reach)."""
    from tools.places.seat import STEP
    hs = [h for gx in range(math.floor((cx - rad) / STEP), math.ceil((cx + rad) / STEP) + 1)
          for gy in range(math.floor((cy - rad) / STEP), math.ceil((cy + rad) / STEP) + 1)
          if math.dist((gx * STEP, gy * STEP), (cx, cy)) <= rad and (h := G.vertex(gx, gy)) is not None]
    return max(hs) - min(hs) if hs else 0.0


def offset(t: dict, base: dict, boxes: list[tuple], given=None, G=None) -> tuple[float, float, float]:
    """(dx, dy, k): the pool's centre off its trunk's and its size as a share of its reach. The place's own offset at
    full size; else, the trunk kept in the sap, the side and size with the lowest score: the bank the dig would leave
    over the sap plus COVER_W times the share hidden from the sky; the centred pool unless that is beaten by more
    than COVER_W * OPEN."""
    if given is not None:
        return float(given[0]), float(given[1]), 1.0
    s = float(t.get("scale", 1.0))
    rad, tr = reach(base, s), trunk_r(base, s)
    x, y = t["pos"][0], t["pos"][1]
    foot = (x, y, tr)

    def bank(o, k):         # what the dig would leave standing over the sap with the pool there (dish's own reckoning)
        if G is None:
            return 0.0
        from tools.places.seat import seat_all
        p = pool_for("", t, base, o, k)
        seat_all([p], G)
        got: list = []
        dish(G, [t, p], {t["base"]: base, POOL: {}}, set(), got)
        return got[0]["bank"] if got else 0.0

    def score(o, k):
        return bank(o, k) + COVER_W * (1.0 - open_share(x + o[0], y + o[1], rad * k, boxes, foot))
    ks = [k for k in SHRINK if k == 1.0 or rad * k >= tr + MIN_BAND]
    cands = [((0.0, 0.0), k) for k in ks] + [
        ((round(d * math.cos(a * math.pi / 4), 1), round(d * math.sin(a * math.pi / 4), 1)), k)
        for k in ks for f in (0.5, 1.0, 1.5) for a in range(8)
        if (d := min(f * max(0.0, rad * k - tr), 0.8 * rad * k)) > 0]           # at most the trunk's foot at the sap's edge
    if G is None and open_share(x, y, rad, boxes) >= 1.0:   # no deck over the pool on its trunk: it stays there
        return 0.0, 0.0, 1.0
    s0 = score((0.0, 0.0), 1.0)
    (o, k), best = min(((c, score(*c)) for c in cands), key=lambda cs: (round(cs[1], 1), -cs[0][1], math.hypot(*cs[0][0])))
    return (o[0], o[1], k) if best < s0 - COVER_W * OPEN + 1e-9 else (0.0, 0.0, 1.0)


def given_for(t: dict, v):
    """A place's per-Hist value (`draft.sap.offset` or `.scale`): the Hist's own entry of a dict, else the value."""
    return v.get(t["id"].split(".", 1)[-1], v.get(t["id"])) if isinstance(v, dict) else v


def plan(place_id: str, ext: list[dict], bases: dict, offsets=None, G=None, scales=None, log=None,
         none=None) -> list[dict]:
    """A pool for every living Hist row of a place's exterior, in row id order; a Hist already standing in a pool
    placed by hand (`draft.add`, the studio) keeps that one. offsets, scales: the place's `draft.sap.offset` and
    `draft.sap.scale`; an offset with a scale is a pool placed by hand, taken as it stands."""
    own = [r for r in ext if r.get("base") == POOL and ".sap." not in r["id"]]
    boxes = covers(ext, bases)
    out = []
    for t in sorted(pooled(ext, bases, none), key=lambda r: r["id"]):
        if any(holds(p, t) for p in own):
            continue
        given, sc = given_for(t, offsets), given_for(t, scales)
        if given is not None and sc is not None:
            p = pool_for(place_id, t, bases[t["base"]], (float(given[0]), float(given[1])), scale=float(sc))
            p["why"] += f"; placed by hand (draft.sap.offset {list(given)}, scale {sc})"
            if log:
                log(f"draft sap {place_id}: {p['id']}: hand-placed at offset {list(given)}, scale {sc} (not scored)")
            out.append(p)
            continue
        dx, dy, k = offset(t, bases[t["base"]], boxes, given, G)
        out.append(pool_for(place_id, t, bases[t["base"]], (dx, dy), k))
    return out


def pooled(ext: list[dict], bases: dict, none=None) -> list[dict]:
    """The living Hists that stand in a pool of their own: every Hist tree and trunk, and a gland only where it grows
    apart from them (a gland within a tree's pool is a growth of that tree, and its sap is the tree's pool); none: the
    place's `draft.sap.none` {Hist ref id: why it has no pool} (no open level ground at its foot), left out."""
    none = {str(k).split(".", 1)[-1] for k in (none or {})}
    hists = [t for t in ext if living(bases.get(t["base"])) and t.get("kind") != "door"
             and t["id"].split(".", 1)[-1] not in none]
    trees = [t for t in hists if "Gland" not in str(bases[t["base"]].get("edid"))]
    reach = [(t, POOL_HALF * pool_for("", t, bases[t["base"]])["scale"]) for t in trees]
    return trees + [g for g in hists if g not in trees
                    and not any(math.dist(g["pos"][:2], t["pos"][:2]) <= r for t, r in reach)]


def faults(ext: list[dict], bases: dict, none=None) -> list[str]:
    """A living Hist without a sap pool holding its trunk, and a stage pool whose Hist is gone."""
    pools = [r for r in ext if r.get("base") == POOL]
    out = []
    hists = [t for t in ext if living(bases.get(t["base"]))]
    for t in pooled(ext, bases, none):
        if not any(of_hist(p, t) for p in pools):
            out.append(f"{t['id']}: a Hist without its sap pool")
    ids = {t["id"].split(".", 1)[-1] for t in hists}
    for p in pools:
        if ".sap." in p["id"] and p["id"].split(".sap.", 1)[1] not in ids:
            out.append(f"{p['id']}: its Hist is gone")
    return out


def hold_others(ext: list[dict], G) -> list[str]:
    """Every row but a pool whose seat reads the ground keeps the height it stands at on the dug ground (its seat's
    dz pinned to its z), so the dig never moves another row; returns the ids pinned."""
    from tools.places.seat import pin, seat_z
    out = []
    for r in ext:
        sd = r.get("seat") or {}
        if r.get("base") == POOL or sd.get("mode") not in ("above", "ground", "stilts", "clear"):
            continue
        if abs(seat_z(r, G) - r["pos"][2]) > 0.5:
            r["seat"] = pin(r, r["pos"][2], G)
            out.append(r["id"])
    return out


def dish(G, ext: list[dict], bases: dict, taken: set, banks: list | None = None, surfaces: dict | None = None) -> list[dict]:
    """Land rows (`by` "sap") that lower the ground inside every pool holding a living Hist to under its surface (its
    floor: its seat's lowest ground or water) and the rim one vertex round it to RIM_LIP over the surface, each vertex
    no more than PATCH_MAX; cells in `taken` (another row's) are left alone. `banks` gets, per pool, what the dig
    limit left standing over the surface on its high side; `surfaces` gets each pool's surface (its lowest rim)."""
    from tools.places.draft.fit import WATERLINE_GAP
    from tools.places.seat import STEP, reference_z
    hists = [t for t in ext if living(bases.get(t["base"]))]
    cells: dict[tuple, dict] = {}
    for p in sorted(ext, key=lambda r: r["id"]):
        if p.get("base") != POOL or not any(of_hist(p, t) for t in hists):
            continue
        sd = p.get("seat") or {}
        floor = reference_z(G, "stilts", p["pos"][0], p["pos"][1], float(p["rot"][2]), sd.get("foot"))
        if floor is None:
            continue
        rad = DISH * POOL_HALF * float(p.get("scale", 1.0))   # the sap's own outline, as a round hollow
        cx, cy = centre(p)
        # the floor is the lowest point any seat sample could read (every vertex up to two past the hollow), so the
        # pool seated again on the dug ground sits on the floor and a second dig changes nothing
        for gx in range(math.floor((cx - rad) / STEP) - 2, math.ceil((cx + rad) / STEP) + 3):
            for gy in range(math.floor((cy - rad) / STEP) - 2, math.ceil((cy + rad) / STEP) + 3):
                h = G.vertex(gx, gy)
                if h is not None and math.dist((gx * STEP, gy * STEP), (cx, cy)) <= rad + 2 * STEP:
                    w = G.water(gx * STEP, gy * STEP)
                    floor = min(floor, max(h, w) if w is not None else h)
        surface, left = floor + DZ, 0.0
        if surfaces is not None:
            surfaces[p["id"]] = surface
        for gx in range(math.floor((cx - rad) / STEP) - 1, math.ceil((cx + rad) / STEP) + 2):
            for gy in range(math.floor((cy - rad) / STEP) - 1, math.ceil((cy + rad) / STEP) + 2):
                d = math.dist((gx * STEP, gy * STEP), (cx, cy))
                if d > rad + STEP:
                    continue
                target = floor if d <= rad else surface + RIM_LIP    # under the sap; the rim level with it
                h = G.vertex(gx, gy)
                if h is None or h <= target:
                    continue
                dz = max(-PATCH_MAX, target - h)
                left = max(left, -(target - h) - PATCH_MAX)
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
        if banks is not None and left > 1:
            banks.append({"pool": p["id"], "bank": round(left, 1)})
    return [{"cell": list(k), "verts": [[r, c, v] for (r, c), v in sorted(vs.items())],
             "why": "the hollow of a Hist's sap pool", "by": "sap"} for k, vs in sorted(cells.items()) if vs]


def settle(pools: list[dict], G, surfaces: dict) -> None:
    """Each pool on the dug ground at the surface its dig was made for (its seat's dz pinned to it), so a sample of
    the dug ground between vertices never stands the sap over its own rim."""
    from tools.places.seat import pin, seat_all
    for p in pools:
        if p["id"] in surfaces:
            p["seat"] = pin(dict(p, seat=dict(p.get("seat") or {"mode": "stilts"}, dz=DZ)), surfaces[p["id"]], G)
    seat_all(pools, G)


def apply(st, log=print) -> None:
    """The `sap` stage: the place's sap pools made again from its standing Hist trees, and their hollows; place.json's
    `sap` lists the pools. A pool row the owner's studio save touched is the owner's (the stage runner keeps it)."""
    from tools.places.seat import Ground, seat_all
    rows, bases = want(st, log)
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
    banks: list = []
    surfaces: dict = {}
    hollow = dish(G, st.ext, {**st.bases, **bases}, {tuple(r["cell"]) for r in other if r.get("by") != "ground"}, banks,
                  surfaces)
    st.files["land"][:] = other + hollow
    G.apply_patches(hollow)
    st.G = G
    settle(pools, G, surfaces)              # the pools at their lowest rims
    held = hold_others(st.ext, G)           # nothing else is moved by the dig
    if held:
        log(f"draft sap {st.place_id}: {len(held)} rows on dug or undug ground keep their height (seats pinned)")
    for b in banks:
        log(f"draft sap {st.place_id}: {b['pool']}: the ground falls more than the dig limit across the pool; "
            f"its high side keeps a bank of {b['bank']} standing out of the sap")
    st.place["sap"] = {"added": [{"id": r["id"], "on": r["id"].split(".sap.", 1)[1]} for r in rows]}
    if POOL in bases:
        st.bases[POOL] = bases[POOL]
    log(f"draft sap {st.place_id}: {len(rows)} sap pools, hollows in {len(hollow)} cells")


def want(st, log=None) -> tuple[list[dict], dict]:
    from tools.places.seat import Ground
    G = Ground.load(st.grd.path)
    G.apply_patches([r for r in st.files["land"] if r.get("by") != "sap"])   # the ground before the dig
    d = (st.place.get("draft") or {}).get("sap") or {}
    return rows_for(st.place_id, st.ext, st.bases, d.get("offset"), G, d.get("scale"), log, d.get("none"))


def rows_for(place_id: str, ext: list[dict], bases: dict, offsets=None, G=None, scales=None,
             log=None, none=None) -> tuple[list[dict], dict]:
    """Pool rows for a place's exterior rows, and the bases with the pool's (none when the catalogue lacks it)."""
    from tools.places.draft.io import catalogue_bases
    bases = dict(bases)
    bases.update(catalogue_bases({POOL} - set(bases)))
    if POOL not in bases:
        return [], bases
    return plan(place_id, ext, bases, offsets, G, scales, log, none), bases


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("place_id")
    a = ap.parse_args(argv)
    from tools.places.draft.stages import Standing
    rows, _ = want(Standing(a.place_id), print)
    print(f"sap {a.place_id} (dry run): {len(rows)} pools")
    for r in rows:
        print(f"  {r['id']} at {r['pos'][:2]} scale {r['scale']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
