"""The BM&V shell census: every building BM&V places in a settlement's exterior cells, as a room a quest or a home can
use without a load door. BM&V's towns stand vanilla and modders' house shells (Solitude, Markarth, farmhouses, Bosmer
tree houses, ships) with few load doors; many are hollow and walkable from the street. For each building ref this
records where it stands, its footprint, and what the load order's winning navmesh says about its inside: how many
navmesh triangles lie inside the footprint, how many of those join the navmesh outside it, on how many floor levels,
and how far the building's origin is sunk below the ground around it. Rows go to `bmv_shell` (story data); the
owner's in-game verdict on a shell is the one column a rebuild keeps.

    python3 -m tools.argonia_world.bmv_shell build  [--dir DIR] [--masters DIR]
    python3 -m tools.argonia_world.bmv_shell verify [--dir DIR] [--masters DIR]   # completeness: rows + exclusions

Class, from the navmesh (a proxy, not proof: the owner's walk is the proof):
  A  navmesh inside the footprint joined to the navmesh outside, >= 10 triangles (walk in from the street)
  B  1 to 9 inside triangles joined to the outside (a doorway or a porch; look)
  C  navmesh inside, none of it joined to the outside (a room you cannot reach, or a roof)
  D  no navmesh inside (solid; or the place has no navmesh at all: then `navmesh_around` is false and D says nothing)
  X  a walkway or platform (docks, Bosmer walkways, decks): not a room

Geometry (Skyrim's convention, as tools/ArgoniaPlugin/Surface.cs): a ref's world point is pos + Rz(-rz) * local * scale,
so a world point comes to local by Rz(+rz). The footprint is the base's OBND x/y box times the scale; Z tilt is ignored
(buildings stand upright). Inside means a triangle's centroid lies within CORE of the footprint's half extents (the
walls' thickness kept out) and within its height band; the ring outside is 1.0 to RING half extents. Joined means a
path of triangles sharing an edge (vertices equal to the unit, across navmeshes) runs from an inside triangle to a ring
triangle without leaving the footprint and ring.
"""
from __future__ import annotations

import argparse
import math
import re
import statistics
import struct
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

from tools.argonia_world import bmv_census as bc
from tools.argonia_world import db

TABLE = "bmv_shell"
CORE = 0.6          # inside: within 60% of the half extents (a wall is not a room)
RING = 1.4          # the ring outside: 1.0 to 1.4 half extents
GROUND_RING = (1.1, 1.5)   # where the ground level around a building is read
NEAR = 1024.0       # the triangle grid's square
LEVEL = 150.0       # units between floor levels
JOINED_A = 10       # joined triangles for class A
MIN_SIDE = 200.0    # footprint's shorter side, units (2.9 m): smaller is not a room
MIN_HEIGHT = 100.0
UNITS_M = 70.0

# Exclusions, tested in order on the base's model path and editor id (lower case); the first match is the reason.
EXCLUDE = [
    ("nature", r"^landscape\\|flora|plants?\\|\\trees?\\|tree\d|_tree|treegiant|treemere|mushroomplant|"
               r"vurt|tramaroot|algrass|bittergreen|marshmerrow|grass|ivy|rosered|lor\\stonefalls\\morrowind\\plants|"
               r"telvanniroot|1mjytropicalstuff|trdata\\mushrooms|telv_mushroom"),
    ("rock", r"(?<!raven)rock|cliff|boulder|menhir|lavarock|\\altr|alashmire|mountain|stones?\\"),
    ("effect", r"^effects\\|fxwaterfall|fog"),
    ("bridge", r"bridge"),
    ("wall", r"wall|pillar|column|colm|\\arch(?!itecture)|arch\d|archlarge|gate|bulwark|stockade|fence|palisade|corner|"
             r"obgate|redoranbase|elvenarch|sesacellumgate|tusks|spikes"),
    ("stairs", r"stair|steps"),
    ("rubble", r"rubble|ruin(s)?\d|wreck|spidersac|bones|skull|cobra"),
    ("part", r"foundation|overhang|window|balcon|balkon|roof|floorpiece|fixation|acces|lianestronc|branche|"
             r"posts|awning|anwing|framemend|ground|innen|interior\\|fireplace|firepit|well\d|bwell|"
             r"towerbase|shellbase|entr(y|ance)|doorhole|doorl|doorr|connector|_cap_|facade|templeinnerring|"
             r"templeouterring|monument|hillside|rootbase|stonebase|_int\.nif|houseint|smallhouseint|floor\.nif|fullinterior"),
    ("clutter", r"^clutter\\|cage|barrel|statue|shrine|obelisk|trebuchet|siege|market ?stand|boatrack|"
                r"fishrack|henhouse|_fan\.nif|bodiespile|standingstone|deity|slab|scaffold|jaegerstand|fountain|pagoda|"
                r"platformbridge|lighthousefire|anim01|\\daedric\\|apocrypha|sovbone|prototype|"
                r"\\animated\\|dragonbones|classic_statue|clothes\\"),
]
WALKWAY = r"walk|pylon|floorlg|\\docks?\\|dock\d|dockstr|dockpier|pier|passerelle|platform|plat|decking|deck\d|kiosk"
BUILDING = (r"house|haus|hut|shack|cabin|manor|tower|inn\.nif|tavern|keep|barracks|embassy|chalet|bunkhouse|church|"
            r"guardhouse|scheune|muehle|wirtshaus|stable|temple|dome|dwelling|fort|ship|boat|caravel|carrack|tent|"
            r"shed|mausoleum|lighthouse|gazebo|chapel|building|mainhall|thronehall|castle|holzhaus|fachwerk|"
            r"bauernhaus|cyrlc|cyrupper|alhut|manorext|inn|warship")
EX = [(n, re.compile(p)) for n, p in EXCLUDE]
WALK = re.compile(WALKWAY)
BUILD = re.compile(BUILDING)
REASONS = ["disabled", "no bounds", "small"] + [n for n, _ in EXCLUDE] + ["not a building"]


def kind(model: str | None, edid: str | None) -> tuple[str, str | None]:
    """('row', 'X'|None) for a building or walkway, ('excluded', reason) for anything else (size not tested here)."""
    s = (model or "").lower().replace("/", "\\") + " " + (edid or "").lower()
    for n, p in EX:
        if p.search(s):
            return "excluded", n
    if WALK.search(s):
        return "row", "X"
    if BUILD.search(s):
        return "row", None
    return "excluded", "not a building"


# --- geometry (pure; the unit tests drive these) ----------------------------------------------------------------------

def footprint(obnd: tuple, scale: float) -> tuple[float, float, float, float, float, float]:
    """The base's bounds times the scale: (x0, y0, z0, x1, y1, z1) in the ref's local frame."""
    return tuple(v * scale for v in obnd)


def to_local(pos: tuple, rz: float, x: float, y: float) -> tuple[float, float]:
    """A world point in the ref's local x/y (Skyrim turns clockwise: world = pos + Rz(-rz) * local)."""
    dx, dy = x - pos[0], y - pos[1]
    c, s = math.cos(rz), math.sin(rz)
    return dx * c - dy * s, dx * s + dy * c


def to_world(pos: tuple, rz: float, lx: float, ly: float) -> tuple[float, float]:
    c, s = math.cos(rz), math.sin(rz)
    return pos[0] + lx * c + ly * s, pos[1] - lx * s + ly * c


def reach(pos: tuple, rz: float, fp: tuple, x: float, y: float) -> float:
    """How far out a point lies, in half extents of the footprint from its centre (<= 1 is inside)."""
    lx, ly = to_local(pos, rz, x, y)
    cx, cy = (fp[0] + fp[3]) / 2, (fp[1] + fp[4]) / 2
    hw, hh = max((fp[3] - fp[0]) / 2, 1e-6), max((fp[4] - fp[1]) / 2, 1e-6)
    return max(abs(lx - cx) / hw, abs(ly - cy) / hh)


def centroid(t: tuple) -> tuple[float, float, float]:
    a, b, c = t
    return (a[0] + b[0] + c[0]) / 3, (a[1] + b[1] + c[1]) / 3, (a[2] + b[2] + c[2]) / 3


def edges(t: tuple) -> list[tuple]:
    k = [tuple(round(v) for v in p) for p in t]
    return [tuple(sorted((k[i], k[(i + 1) % 3]))) for i in range(3)]


def measure(pos: tuple, rz: float, fp: tuple, tris: list[tuple]) -> dict:
    """Inside, joined, floor levels, ground and the navmesh most of the inside lies on, from the triangles near a
    ref: each (v0, v1, v2, navmesh key) with world vertices."""
    z0, z1 = pos[2] + fp[2] - 100, pos[2] + fp[5] + 50
    rel, cen = {}, {}
    for i, t in enumerate(tris):
        c = centroid(t[:3])
        cen[i], rel[i] = c, reach(pos, rz, fp, c[0], c[1])
    core = {i for i in rel if rel[i] <= CORE and z0 <= cen[i][2] <= z1}
    zone = {i for i in rel if rel[i] <= RING}
    ring = {i for i in zone if rel[i] > 1.0}
    adj = defaultdict(list)
    for i in zone:
        for e in edges(tris[i][:3]):
            adj[e].append(i)
    nb = defaultdict(set)
    for ts in adj.values():
        for i in ts:
            nb[i].update(j for j in ts if j != i)
    joined, seen = 0, set()
    for s in core:
        if s in seen:
            continue
        comp, todo = {s}, [s]
        while todo:
            u = todo.pop()
            for v in nb[u]:
                if v not in comp:
                    comp.add(v)
                    todo.append(v)
        seen |= comp
        if comp & ring:
            joined += len(comp & core)
    g = [cen[i][2] for i in rel if GROUND_RING[0] <= rel[i] <= GROUND_RING[1]]
    ground = statistics.median(g) if g else None
    navs = Counter(tris[i][3] for i in core)
    return {"inner_tris": len(core), "joined_tris": joined, "ring_tris": len(ring),
            "floor_levels": len({round(cen[i][2] / LEVEL) for i in core}),
            "ground_z": round(ground, 1) if ground is not None else None,
            "navmesh": navs.most_common(1)[0][0] if navs else None}


def klass(m: dict, walkway: bool) -> str:
    if walkway:
        return "X"
    if m["joined_tris"] >= JOINED_A:
        return "A"
    if m["joined_tris"]:
        return "B"
    return "C" if m["inner_tris"] else "D"


# --- reading the load order -------------------------------------------------------------------------------------------

def nvnm(d: bytes) -> tuple[list, list]:
    """A NAVM's vertices and triangles (vertex index triples) from its NVNM."""
    o = 16
    nv = struct.unpack_from("<I", d, o)[0]
    o += 4
    V = [struct.unpack_from("<3f", d, o + 12 * i) for i in range(nv)]
    o += 12 * nv
    nt = struct.unpack_from("<I", d, o)[0]
    o += 4
    T = [struct.unpack_from("<3H", d, o + 16 * i) for i in range(nt)]
    return V, [t for t in T if max(t) < nv]


class Navmesh:
    """Every winning NAVM's triangles in a worldspace, on a grid for lookups near a point."""

    def __init__(self, L: bc.Load, worlds: set[str]):
        self.grid: dict[tuple, list] = defaultdict(list)
        self.count = 0
        for r in L.live("NAVM"):
            ws = L.world_key(r)
            d = r.sub("NVNM")
            if ws not in worlds or not d:
                continue
            V, T = nvnm(d)
            for t in T:
                tri = (V[t[0]], V[t[1]], V[t[2]], r.key)
                c = centroid(tri[:3])
                self.grid[(ws, int(c[0] // NEAR), int(c[1] // NEAR))].append(tri)
                self.count += 1

    def near(self, ws: str, x: float, y: float, r: float) -> list:
        out = []
        for gx in range(int((x - r) // NEAR), int((x + r) // NEAR) + 1):
            for gy in range(int((y - r) // NEAR), int((y + r) // NEAR) + 1):
                out += self.grid.get((ws, gx, gy), [])
        return out


def candidates(L: bc.Load, masters: Path, w) -> tuple[list[dict], Counter, dict]:
    """Every STAT or SCOL ref the load order places in a settlement's exterior cells: the rows to measure, and the
    excluded counted by (settlement, reason)."""
    res = bc.Resolver(L, masters, {"STAT", "SCOL"})
    cells = {r[0]: (r[1], r[2]) for r in w.query(
        "SELECT sc.cell, sc.settlement, c.worldspace FROM bmv_settlement_cell sc JOIN bmv_cell c ON c.id = sc.cell "
        "WHERE c.interior = 0")}
    rows, excl, total = [], Counter(), Counter()
    for r in L.live("REFR"):
        ck = L.cell_key(r)
        if ck not in cells:
            continue
        b = res.win.get(r.ref("NAME"))
        if b is None or b.sig not in ("STAT", "SCOL"):
            continue
        sid, ws = cells[ck]
        total[sid] += 1
        o = b.sub("OBND")
        model = b.zstr("MODL")
        x, y, z, rx, ry, rz = struct.unpack_from("<6f", r.sub("DATA"))
        xs = r.sub("XSCL")
        scale = struct.unpack("<f", xs)[0] if xs else 1.0
        what, why = kind(model, b.edid)
        fp = footprint(struct.unpack("<6h", o), scale) if o else None
        if r.flags & bc.DISABLED:
            reason = "disabled"
        elif fp is None:
            reason = "no bounds"
        elif what == "excluded":
            reason = why
        elif min(fp[3] - fp[0], fp[4] - fp[1]) < MIN_SIDE or fp[5] - fp[2] < MIN_HEIGHT:
            reason = "small"
        else:
            reason = None
        if reason:
            excl[(sid, reason)] += 1
            continue
        rows.append({"id": r.key, "settlement": sid, "worldspace": ws, "cell": ck, "base": b.key,
                     "base_editor_id": b.edid, "model": model, "x": x, "y": y, "z": z, "rot": (rx, ry, rz),
                     "scale": scale, "fp": fp, "walkway": why == "X"})
    return rows, excl, total


def census(d: Path, masters: Path, w) -> tuple[list[dict], Counter, Counter]:
    L = bc.Load(d)
    cand, excl, total = candidates(L, masters, w)
    nav = Navmesh(L, {c["worldspace"] for c in cand})
    doors = defaultdict(list)
    for r in w.query("SELECT id, worldspace, x, y FROM bmv_door WHERE worldspace IS NOT NULL"):
        doors[r[1]].append((r[0], r[2], r[3]))
    out = []
    for c in cand:
        pos, rz, fp = (c["x"], c["y"], c["z"]), c["rot"][2], c["fp"]
        half = math.hypot(abs(fp[0] + fp[3]) / 2 + (fp[3] - fp[0]) / 2 * GROUND_RING[1],
                          abs(fp[1] + fp[4]) / 2 + (fp[4] - fp[1]) / 2 * GROUND_RING[1])
        m = measure(pos, rz, fp, nav.near(c["worldspace"], c["x"], c["y"], half))
        near = min(((math.hypot(x - c["x"], y - c["y"]), k) for k, x, y in doors[c["worldspace"]]), default=None)
        out.append({
            "id": c["id"], "settlement": c["settlement"], "worldspace": c["worldspace"], "cell": c["cell"],
            "base": c["base"], "base_editor_id": c["base_editor_id"], "model": c["model"],
            "x": round(c["x"], 1), "y": round(c["y"], 1), "z": round(c["z"], 1),
            "rot_x": round(math.degrees(c["rot"][0]), 1), "rot_y": round(math.degrees(c["rot"][1]), 1),
            "rot_z": round(math.degrees(rz) % 360, 1), "scale": round(c["scale"], 3),
            "footprint_w_m": round((fp[3] - fp[0]) / UNITS_M, 1), "footprint_d_m": round((fp[4] - fp[1]) / UNITS_M, 1),
            "height_m": round((fp[5] - fp[2]) / UNITS_M, 1), "class": klass(m, c["walkway"]),
            "inner_tris": m["inner_tris"], "joined_tris": m["joined_tris"], "floor_levels": m["floor_levels"],
            "ground_z": m["ground_z"], "navmesh_around": m["ring_tris"] > 0,
            "sunk_m": round((m["ground_z"] - c["z"]) / UNITS_M, 1) if m["ground_z"] is not None else None,
            "navmesh": m["navmesh"], "door": near[1] if near else None,
            "door_m": round(near[0] / UNITS_M) if near else None, "owner_verdict": None})
    return out, excl, total


def build(d: Path, masters: Path) -> tuple[list[dict], Counter, Counter]:
    w = db.load(strict=False)      # a schema change leaves old shell rows unloadable; they are replaced here
    rows, excl, total = census(d, masters, w)
    kept = {r[0]: r[1] for r in w.query(f'SELECT id, owner_verdict FROM "{TABLE}" WHERE owner_verdict IS NOT NULL')}
    for r in rows:
        r["owner_verdict"] = kept.get(r["id"])
    lost = set(kept) - {r["id"] for r in rows}
    if lost:
        raise SystemExit(f"owner verdicts on {len(lost)} shells no longer found, e.g. {sorted(lost)[:3]}: "
                         "settle them before a rebuild")
    w._begin()
    w.con.execute(f'DELETE FROM "{TABLE}"')
    w.dirty.add(TABLE)
    w.insert_many(TABLE, rows)
    w.save()
    return rows, excl, total


def proof(d: Path, masters: Path) -> tuple[list[str], list[str]]:
    """Per settlement: STAT/SCOL refs in its exterior cells = shell rows + excluded by reason; the table's rows are
    exactly those the files give now, with the same settlement and class."""
    w = db.load()
    rows, excl, total = census(d, masters, w)
    have = {r[0]: (r[1], r[2]) for r in w.query(f'SELECT id, settlement, class FROM "{TABLE}"')}
    want = {r["id"]: (r["settlement"], r["class"]) for r in rows}
    bad = []
    if set(have) != set(want):
        bad.append(f"rows differ: {len(set(want) - set(have))} missing, {len(set(have) - set(want))} extra, e.g. "
                   f"{sorted(set(want) ^ set(have))[:3]}")
    diff = [k for k in set(have) & set(want) if have[k] != want[k]]
    if diff:
        bad.append(f"{len(diff)} rows changed settlement or class, e.g. {sorted(diff)[:3]}")
    per = Counter(r["settlement"] for r in rows)
    lines = ["settlement\trefs\trows\t" + "\t".join(REASONS)]
    for sid in sorted(total):
        ex = [excl[(sid, n)] for n in REASONS]
        if total[sid] != per[sid] + sum(ex):
            bad.append(f"{sid}: {total[sid]} refs != {per[sid]} rows + {sum(ex)} excluded")
        lines.append(f"{sid}\t{total[sid]}\t{per[sid]}\t" + "\t".join(map(str, ex)))
    lines.append(f"all\t{sum(total.values())}\t{len(rows)}\t" +
                 "\t".join(str(sum(v for (_, n), v in excl.items() if n == r)) for r in REASONS))
    sett = set(w.values("SELECT id FROM bmv_settlement"))
    lines.append(f"settlements with exterior cells: {len(total)} of {len(sett)} (sites have interiors only)")
    return lines, bad


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("cmd", choices=["build", "verify"])
    ap.add_argument("--dir", type=Path, default=bc.DIR)
    ap.add_argument("--masters", type=Path, default=bc.MASTERS)
    a = ap.parse_args(argv)
    t = time.time()
    if a.cmd == "build":
        rows, excl, total = build(a.dir, a.masters)
        print(f"{len(rows)} shells of {sum(total.values())} STAT/SCOL refs in {len(total)} settlements; "
              f"class {dict(sorted(Counter(r['class'] for r in rows).items()))}; {time.time() - t:.0f} s")
        return 0
    lines, bad = proof(a.dir, a.masters)
    print("\n".join(lines))
    print("\n".join(bad) or f"every STAT/SCOL ref is a shell or excluded with a reason ({time.time() - t:.0f} s)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
