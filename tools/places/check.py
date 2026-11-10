"""Read the built place layer back and fail on each item of the contract's check list (place-studio.md, Build).

    python -m tools.places check <place_id> [--out DIR] [--json]

Reads out/places/plugin/ArgoniaNWPlaces.esp (records by tools/ArgoniaPlaces/Build `dump`, navmesh by its bytes),
the place's shard plan (which records are this place's, and its place files' rows), the world ESM's facts round the
place (ground, refs) and the world's own navmesh beside ours. Exit 1 when any check fails; every check is a
function of one context dict, so tools/tests can feed it a small broken fixture each.

Checks: seat, overlap, doors, people, navmesh, land, clear, services, nordic, levelled, plugin (masters, links).
"""
from __future__ import annotations

import argparse
import base64
import gzip
import json
import math
import re
import struct
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

from tools.places import build as B

SEAT_TOL = 8.0  # units: one VHGT step
STOP_PLAN_TOL, STOP_Z_TOL = 96.0, 128.0  # a routine stop or arrival point is on navmesh within these
OVERLAP_SHRINK = 0.8  # a ref is inside another's collision when its origin is within this share of the other's box
PLANT_DOOR_CLEAR = 128.0
SOLID = {"building", "static", "furniture", "container", "door", "activator", "rock"}
PLANT_TYPES = {"TREE", "FLOR"}
# Nordic: a base whose model or editor id is of Skyrim's Nordic culture (decision 0006). Paths are Skyrim.esm's own
# folders for the hold cities, Nordic farms and ruins; editor-id prefixes are the CK's for the same kits.
NORDIC_MODEL = re.compile(r"(^|/)(architecture/(whiterun|windhelm|solitude|markarth|riften|farmhouse|winterhold|dawnstar|"
                          r"falkreath|morthal|riverwood|nordic|nordichall)|dungeons/nordic|clutter/nordic|furniture/nordic|"
                          r"clutter/(?:[a-z]*/)?(?:talos|shrineoftalos)|/nord[a-z]*\d|/wr[a-z]+\d|/wh[a-z]+\d)", re.I)
NORDIC_EDID = re.compile(r"^(Nor[A-Z]|Nord|WR[A-Z]|WH[A-Z]|Whiterun|Windhelm|Solitude|Markarth|Riften|Farmhouse|Talos)", re.U)
CRAFT_KEYWORD = {"forge": "CraftingSmithingForge", "anvil": "CraftingSmithingForge", "armour-workbench": "CraftingSmithingArmorTable",
                 "grindstone": "CraftingSmithingSharpeningWheel", "smelter": "CraftingSmelter", "tanning-rack": "CraftingTanningRack",
                 "alchemy-lab": "WICraftingAlchemy", "arcane-enchanter": "WICraftingEnchanting", "cooking-pot": "CraftingCookpot",
                 "oven": "BYOHCraftingOven", "staff-enchanter": "DLC2StaffEnchanter"}
TRADE_JOB = {"trader-general": "JobMerchantFaction", "trader-blacksmith": "JobBlacksmithFaction", "trader-apothecary": "JobApothecaryFaction",
             "trader-spells": "JobSpellFaction", "trader-innkeeper": "JobInnkeeperFaction", "trader-fletcher": "JobFletcherFaction",
             "trader-jeweller": "JobJewelerFaction", "trader-clothier": "JobTailorFaction", "trader-hunter": "JobMiscFaction",
             "trader-bookseller": "JobMiscFaction", "fence": "JobFenceFaction"}
NOT_A_PLACE_SERVICE = {"combat-foes", "combat-boss", "combat-creature", "treasure", "boss-chest", "gold-hoard", "unique-item",
                       "harvest-common", "harvest-rare", "fishing", "ore-vein", "skill-book", "spell-tome", "word-wall",
                       "standing-stone", "free-bed", "follower", "player-home", "altar-power"}


# ---- geometry -------------------------------------------------------------------------------------------------------

def obb_contains(ref: dict, p, shrink: float = 1.0) -> bool:
    b = ref.get("bounds")
    if not b:
        return False
    R = B.rotation(*ref["rot"]) * float(ref.get("scale") or 1.0)
    local = np.linalg.solve(R, np.asarray(p, float) - np.asarray(ref["pos"], float))
    lo, hi = np.array(b[:3], float), np.array(b[3:], float)
    c, h = (lo + hi) / 2, (hi - lo) / 2 * np.array([shrink, shrink, 1.0])  # shrunk in plan; the full height (origins sit on the floor)
    return bool(np.all(np.abs(local - c) <= h + np.array([0.0, 0.0, 1.0])))


def point_seg(p, a, b) -> float:
    return float(B.seg_dist(p[0], p[1], a[0], a[1], b[0], b[1]))


class Nav:
    """One navmesh decoded: verts, triangles, internal neighbours, edge links and door triangles."""

    def __init__(self, fk: str, space: str, cell, nv, key_of_raw):
        self.fk, self.space, self.cell = fk, space, cell
        self.verts = np.asarray(nv.verts, float)
        self.tri = nv.tris["v"].astype(int)
        self.flags = nv.tris["flags"].astype(int)
        self.edge = nv.tris["e"].astype(int)
        self.links = [(int(ln["type"]), key_of_raw(int(ln["navm"])), int(ln["tri"])) for ln in nv.links]
        self.doors = [(int(d["tri"]), key_of_raw(int(d["door"]))) for d in nv.doors]

    def tri_at(self, p, plan_tol=STOP_PLAN_TOL, z_tol=STOP_Z_TOL) -> int:
        v = self.verts
        best, bd = -1, float("inf")
        for i, t in enumerate(self.tri):
            a, b, c = v[t[0]], v[t[1]], v[t[2]]
            d1 = (p[0] - b[0]) * (a[1] - b[1]) - (a[0] - b[0]) * (p[1] - b[1])
            d2 = (p[0] - c[0]) * (b[1] - c[1]) - (b[0] - c[0]) * (p[1] - c[1])
            d3 = (p[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (p[1] - a[1])
            inside = not ((d1 < 0 or d2 < 0 or d3 < 0) and (d1 > 0 or d2 > 0 or d3 > 0))
            dp = 0.0 if inside else min(point_seg(p, a, b), point_seg(p, b, c), point_seg(p, c, a))
            dz = abs((a[2] + b[2] + c[2]) / 3 - p[2])
            if dp <= plan_tol and dz <= z_tol and dp + dz * 0.01 < bd:
                best, bd = i, dp + dz * 0.01
        return best


def components(navs: dict[str, Nav], door_pairs: dict[str, str]) -> dict[tuple[str, int], int]:
    """Connected components over every triangle: shared edges, edge links, and door triangles of paired doors."""
    parent: dict = {}

    def find(x):
        while parent.setdefault(x, x) != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    door_tris: dict[str, list] = defaultdict(list)
    for n in navs.values():
        for i in range(len(n.tri)):
            find((n.fk, i))
            for k in range(3):
                e = int(n.edge[i][k])
                if n.flags[i] & (1 << k):
                    if 0 <= e < len(n.links):
                        _, tgt, tt = n.links[e]
                        if tgt in navs:
                            union((n.fk, i), (tgt, tt))
                elif e >= 0:
                    union((n.fk, i), (n.fk, e))
        for ti, door in n.doors:
            door_tris[door].append((n.fk, ti))
    for d, partner in door_pairs.items():
        for a in door_tris.get(d, []):
            for b in door_tris.get(partner, []):
                union(a, b)
    return {k: find(k) for k in list(parent)}


# ---- loading --------------------------------------------------------------------------------------------------------

def load_navs(esp: Path, world_rows: dict) -> dict[str, Nav]:
    from tools.navmesh import esm, nvnm
    masters = esm.masters(esp)
    names = masters + [B.PLUGIN]

    def key_of_raw(raw: int) -> str:
        i = raw >> 24
        return B.key_of(names[i] if i < len(names) else "?", raw & 0xFFFFFF)

    cells = {}
    out = {}
    for rec in esm.records(esp, {b"NAVM", b"CELL"}):
        if rec.sig == b"CELL":
            continue
        nv = nvnm.decode(next(p for s, p in esm.subrecords(rec.data) if s == b"NVNM"))
        fk = key_of_raw(rec.fid)
        space = "exterior" if nv.world else key_of_raw(nv.cell)
        out[fk] = Nav(fk, space, nv.grid_xy, nv, key_of_raw)
        cells[fk] = nv.grid_xy
    # the world's navmesh round ours (for links out of ours, and stops outside our cells)
    for (x, y), e in world_rows.items():
        rec = base64.b64decode(e["navm"])
        fid = struct.unpack_from("<I", rec, 12)[0]
        fk = B.key_of(B.WORLD, fid & 0xFFFFFF)
        if fk in out:
            continue
        nv = nvnm.decode(next(p for s, p in esm.subrecords(rec[24:]) if s == b"NVNM"))
        wn = ["Skyrim.esm", B.WORLD]
        out[fk] = Nav(fk, "exterior", (x, y), nv, lambda r, wn=wn: B.key_of(wn[r >> 24] if (r >> 24) < 2 else "?", r & 0xFFFFFF))
        out[fk].world = True
    return out


def world_nav_rows(box) -> dict:
    rows = {}
    for p in sorted((B.WORLD_NAV / "navm").glob("cy*.jsonl.gz")):
        cy = int(p.name[2:6])
        if box[1] <= cy <= box[3]:
            for ln in gzip.open(p, "rt"):
                e = json.loads(ln)
                if box[0] <= e["x"] <= box[2]:
                    rows[(e["x"], e["y"])] = e
    return rows


def load(place_id: str, out: Path) -> dict:
    plan = json.loads((out / "shards" / place_id / "plan.json").read_text())
    esp = out / "plugin" / B.PLUGIN
    tmp = out / "tmp" / f"check_{place_id}"
    tmp.mkdir(parents=True, exist_ok=True)
    B.build_tool()
    B.tool("dump", str(esp), str(B.WORLD_ESM), str(tmp / "dump.json"))
    dump = json.loads((tmp / "dump.json").read_text())
    (tmp / "dump.json").unlink()
    cells = {(c["x"], c["y"]) for c in plan["cells"]}
    facts = B.world_facts(cells, tmp)
    tmp.rmdir()
    xs, ys = [c[0] for c in cells] or [0], [c[1] for c in cells] or [0]
    r = B.NAV_RING + 4  # every world mesh a shipped one can link into
    world_rows = world_nav_rows((min(xs) - r, min(ys) - r, max(xs) + r, max(ys) + r))
    navs = load_navs(esp, world_rows)
    edid = {c["fk"]: c["edid"] for c in dump["cells"]}
    for n in navs.values():
        n.space = edid.get(n.space, n.space) if n.space != "exterior" else n.space
    return {"place_id": place_id, "plan": plan, "dump": dump, "facts": facts, "navs": navs, "gives": gives_of(place_id),
            "place_dir": B.PLACES / place_id}


def gives_of(place_id: str) -> list[dict]:
    return [r for r in B.jsonl(B.DB / "place_give.jsonl") if r["place_id"] == place_id]


# ---- the context --------------------------------------------------------------------------------------------------

def mine(ctx: dict) -> dict:
    """This place's records in the read-back, by key."""
    plan, dump = ctx["plan"], ctx["dump"]
    keys = {r["fk"] for r in plan["refs"]}
    ppl = plan.get("people") or {}
    keys |= {m["fk"] for m in ppl.get("markers", [])}
    refs = {r["fk"]: r for r in dump["refs"] if r["fk"] in keys}
    actors = {a["fk"]: a for a in dump["actors"] if a["fk"] in {x["fk"] for x in ppl.get("actors", [])}}
    npcs = {n["fk"]: n for n in dump["npcs"] if n["fk"] in {x["fk"] for x in ppl.get("npcs", [])}}
    return {"refs": refs, "actors": actors, "npcs": npcs, "rows": {r["fk"]: r for r in plan["refs"]}}


def ground(ctx: dict):
    """Ground height at (x, y) from the BUILT land: our LAND override where there is one, else the world's."""
    from tools.newworld.world import quantize
    steps = {}
    for c in ctx["facts"]["cells"]:
        if c.get("deltas"):
            steps[(c["x"], c["y"])] = B.cell_steps(c)
    for L in ctx["dump"]["land"]:
        if L.get("x") is not None:
            d = np.frombuffer(base64.b64decode(L["deltas"]), np.int8).reshape(33, 33)
            steps[(L["x"], L["y"])] = quantize.decode(float(L["offset"]), d)

    def z(x, y):
        cx, cy = B.cell_of(x, y)
        s = steps.get((cx, cy))
        if s is None:
            return None
        fx, fy = (x - cx * B.CELL) / B.QUAD, (y - cy * B.CELL) / B.QUAD
        i, j = min(int(fx), 31), min(int(fy), 31)
        u, v = fx - i, fy - j
        h = (s[j, i] * (1 - u) * (1 - v) + s[j, i + 1] * u * (1 - v) + s[j + 1, i] * (1 - u) * v + s[j + 1, i + 1] * u * v)
        return float(h) * 8.0
    return z, steps


# ---- the checks -----------------------------------------------------------------------------------------------------

def check_plugin(ctx) -> list[str]:
    d = ctx["dump"]
    bad = [f"unresolved link: {u}" for u in d["unresolved"]]
    if B.WORLD not in d["masters"]:
        bad.append(f"not mastered on {B.WORLD}: masters {d['masters']}")
    return bad


def built_ground(ctx):
    """lane D's seat.Ground (the one seating function's view of land and water) over the BUILT land heights."""
    from tools.places import seat as S
    pid = ctx.get("place_id")
    g = S.ground_for(pid) if pid and (S.BUNDLES / f"ground.{pid}").exists() else S.Ground({}, {})  # water: the ground bundle
    _, steps = ground(ctx)
    for (cx, cy), st in steps.items():
        g.cells[(cx, cy)] = [float(v) * 8.0 for v in np.asarray(st, np.float64).reshape(-1)]
    return g


def check_seat(ctx) -> list[str]:
    """Every exterior ref's BUILT z is what seat.seat_z gives at its BUILT x, y, yaw on the built land."""
    from tools.places import seat as S
    g = built_ground(ctx)
    m = mine(ctx)
    built = []
    for r in ctx["plan"]["refs"]:
        if r["space"] != "exterior":
            continue
        got = m["refs"].get(r["fk"])
        if got is None:
            if (r.get("seat") or {}).get("mode", "free") != "free":
                ctx.setdefault("_seat_missing", []).append(f"{r['id']}: not in the plugin")
            continue
        built.append({"id": r["id"], "seat": r.get("seat") or {"mode": "free"}, "pos": list(got["pos"]),
                      "rot": list(r.get("rot") or [0, 0, 0])})
    want = {x["id"]: x["pos"][2] for x in built}
    trial = [dict(x, pos=list(x["pos"])) for x in built]
    S.seat_all(trial, g)
    bad = list(ctx.pop("_seat_missing", []))
    for x in trial:
        if abs(x["pos"][2] - want[x["id"]]) > SEAT_TOL:
            s = x["seat"]
            bad.append(f"{x['id']}: built z {want[x['id']]:.0f}, seat {s.get('mode')}+{s.get('dz', 0)} gives {x['pos'][2]:.0f}")
    return bad


def check_overlap(ctx) -> list[str]:
    m = mine(ctx)
    rows = m["rows"]
    refs = [r for r in m["refs"].values() if rows.get(r["fk"], {}).get("kind") in SOLID]
    bad = []
    by_space = defaultdict(list)
    for r in refs:
        by_space[r["space"]].append(r)
    for sp, rs in by_space.items():
        for a in rs:
            for b in rs:
                if a is b or not b.get("bounds"):
                    continue
                if sp != "exterior" and rows.get(b["fk"], {}).get("kind") in ("building", "static"):
                    continue  # an interior's shell and walls hold the room
                if obb_contains(b, a["pos"], OVERLAP_SHRINK) and not _source_had(rows.get(a["fk"], {}), rows.get(b["fk"], {})):
                    bad.append(f"{rows[a['fk']]['id']} stands inside {rows[b['fk']]['id']}")
    return bad


def _source_had(a: dict, b: dict) -> bool:
    """The source had this pair in this relative pose: both copied, and either inside one copied interior (it keeps its
    frame) or in one exterior cluster (the fit moves a cluster as one rigid piece); or a door stands on its own building."""
    if (a.get("seat") or {}).get("on") == b.get("id") or (b.get("seat") or {}).get("on") == a.get("id"):
        return True
    if not (a.get("src") and b.get("src") and a["space"] == b["space"]):
        return False
    return a["space"] != "exterior" or (a.get("cluster") is not None and a.get("cluster") == b.get("cluster"))


def door_pairs(ctx) -> dict[str, str]:
    return {r["fk"]: r["door"]["to_ref"] for r in mine(ctx)["refs"].values() if r.get("door")}


def check_doors(ctx) -> list[str]:
    m = mine(ctx)
    refs = {**{r["fk"]: r for r in ctx["dump"]["refs"]}}
    bad = []
    for r in m["refs"].values():
        d = r.get("door")
        if not d:
            continue
        rid = m["rows"].get(r["fk"], {}).get("id", r["fk"])
        p = refs.get(d["to_ref"])
        if p is None or not p.get("door") or p["door"]["to_ref"] != r["fk"]:
            bad.append(f"door {rid}: its partner {d['to_ref']} does not lead back")
            continue
        if not r.get("persistent"):
            bad.append(f"door {rid}: a load door must be persistent")
        # the marker by this door (where one lands using the partner): on navmesh, out of every wall
        at = p["door"]["to_pos"]
        space = r["space"]
        on_id = (m["rows"].get(r["fk"], {}).get("seat") or {}).get("on")
        stands_on = next((x["fk"] for x in m["rows"].values() if x.get("id") == on_id), None) if on_id else None
        navs = [n for n in ctx["navs"].values() if n.space == space or (space == "exterior" and n.space == "exterior")]
        if not any(n.tri_at(at) >= 0 for n in navs):
            bad.append(f"door {rid}: its arrival point {[round(v) for v in at]} is on no navmesh (facing a wall?)")
        for o in ctx["dump"]["refs"]:
            kinds = SOLID if space == "exterior" else SOLID - {"building", "static"}  # an interior's shell holds the room
            if o["fk"] == stands_on:
                continue  # the thing the door stands on (its own building) holds the door, not the arrival
            if o["space"] == space and o["fk"] != r["fk"] and m["rows"].get(o["fk"], {}).get("kind") in kinds and obb_contains(o, at, OVERLAP_SHRINK):
                bad.append(f"door {rid}: its arrival point is inside {m['rows'].get(o['fk'], {}).get('id', o['fk'])}")
    return bad


def check_people(ctx) -> list[str]:
    m = mine(ctx)
    ppl = ctx["plan"].get("people") or {}
    allrefs = {r["fk"]: r for r in ctx["dump"]["refs"]}
    pk = {p["fk"]: p for p in ctx["dump"]["packages"]}
    comp = components(ctx["navs"], door_pairs(ctx))
    bad = []

    def where(fk):
        r = allrefs.get(fk)
        if r is None:
            return None
        return r["space"], r["pos"]

    def node(space, pos):
        for n in ctx["navs"].values():
            if n.space == space:
                t = n.tri_at(pos)
                if t >= 0:
                    return (n.fk, t)
        return None

    for n in ppl.get("npcs", []):
        got = m["npcs"].get(n["fk"])
        who = n["id"]
        if got is None:
            bad.append(f"{who}: no actor base in the plugin")
            continue
        beds = [r for r in m["refs"].values() if r.get("owner") == n["fk"] and r.get("base_type") == "FURN"]
        if not beds and n.get("role") != "innkeeper":  # vanilla's innkeepers keep the inn all day (one 24-hour package)
            bad.append(f"{who}: no bed owned")
        prev = None
        for k in got["packages"]:
            p = pk.get(k)
            if p is None:
                bad.append(f"{who}: package {k} missing")
                continue
            tgt = p.get("location") or p.get("target")
            if p.get("target_linked"):  # a patrol, the vanilla way: the actor's own linked ref (no keyword) starts the chain
                act = next((a for a in ctx["dump"]["actors"] if a.get("base") == n["fk"]), {})
                tgt = next((ln["ref"] for ln in act.get("linked") or [] if not ln.get("keyword")), None)
                if tgt is None:
                    bad.append(f"{who}: {p['edid']} patrols its linked ref, but the actor has no linked ref without a keyword")
                    continue
                seen, cur = set(), tgt
                while cur and cur not in seen:  # the chain of markers must be ours and resolve
                    seen.add(cur)
                    r = allrefs.get(cur)
                    if r is None:
                        bad.append(f"{who}: {p['edid']} patrol chain reaches {cur}, which is not a ref of ours")
                        break
                    cur = next((ln["ref"] for ln in r.get("linked") or [] if not ln.get("keyword")), None)
                if len(seen) < 2:
                    bad.append(f"{who}: {p['edid']} patrol chain has fewer than two markers")
            w = where(tgt) if tgt else None
            if w is None:
                bad.append(f"{who}: {p['edid']} has no place of ours")
                continue
            nd = node(*w)
            if nd is None:
                bad.append(f"{who}: {p['edid']} stop {[round(v) for v in w[1]]} in {w[0]} is off the navmesh")
                continue
            if prev is not None and comp.get(prev) != comp.get(nd):
                bad.append(f"{who}: {p['edid']} is not reachable from the stop before")
            prev = nd
    return bad


def check_navmesh(ctx) -> list[str]:
    navs = ctx["navs"]
    mine_navs = {k: n for k, n in navs.items() if not getattr(n, "world", False)}
    bad = []
    # every edge link is answered from the other side (joined edge for edge)
    for n in mine_navs.values():
        for i in range(len(n.tri)):
            for k in range(3):
                if not n.flags[i] & (1 << k):
                    continue
                _, tgt, tt = n.links[int(n.edge[i][k])]
                o = navs.get(tgt)
                if o is None:
                    bad.append(f"{n.fk}: tri {i} links into {tgt}, which is not loaded")
                    continue
                if not 0 <= tt < len(o.tri):
                    bad.append(f"{n.fk}: tri {i} links {tgt} tri {tt}, which {tgt} does not have ({len(o.tri)} triangles)")
                    continue
                if not any(o.flags[tt] & (1 << q) and o.links[int(o.edge[tt][q])][1] == n.fk and o.links[int(o.edge[tt][q])][2] == i for q in range(3)):
                    bad.append(f"{n.fk}: tri {i} links {tgt} tri {tt}, which does not link back (unjoined edge)")
    # open edges of ours on a seam with a neighbour's navmesh across: unjoined
    for n in mine_navs.values():
        if n.space != "exterior" or n.cell is None:
            continue
        x0, y0 = n.cell[0] * B.CELL, n.cell[1] * B.CELL
        for i in range(len(n.tri)):
            for k in range(3):
                if n.flags[i] & (1 << k) or n.edge[i][k] >= 0:
                    continue
                a, b = n.verts[n.tri[i][k]], n.verts[n.tri[i][(k + 1) % 3]]
                on = (abs(a[0] - x0) < 1 and abs(b[0] - x0) < 1) or (abs(a[0] - x0 - B.CELL) < 1 and abs(b[0] - x0 - B.CELL) < 1) or \
                     (abs(a[1] - y0) < 1 and abs(b[1] - y0) < 1) or (abs(a[1] - y0 - B.CELL) < 1 and abs(b[1] - y0 - B.CELL) < 1)
                if on and _across(navs, n, (a + b) / 2):
                    bad.append(f"{n.fk}: open seam edge at {[round(v) for v in (a + b) / 2]} with navmesh across it (unjoined)")
    # islands that hold a door or a routine stop of the place
    comp = components(navs, door_pairs(ctx))
    sizes = defaultdict(int)
    for k, c in comp.items():
        sizes[c] += 1
    main = max(sizes, key=sizes.get) if sizes else None
    m = mine(ctx)
    for r in m["refs"].values():
        if not r.get("door"):
            continue
        for n in mine_navs.values():
            for ti, d in n.doors:
                if d == r["fk"] and comp.get((n.fk, ti)) != main:
                    bad.append(f"door {m['rows'].get(r['fk'], {}).get('id', r['fk'])}: its navmesh is an island ({sizes[comp[(n.fk, ti)]]} triangles)")
    return bad


def _across(navs, n, mid) -> bool:
    for o in navs.values():
        if o is n or o.space != "exterior" or o.cell is None or o.cell == n.cell:
            continue
        if abs(o.cell[0] - n.cell[0]) + abs(o.cell[1] - n.cell[1]) != 1:
            continue
        if o.tri_at(mid, plan_tol=2.0, z_tol=64.0) >= 0:
            return True
    return False


def check_land(ctx) -> list[str]:
    from tools.newworld.world import quantize
    bad = []
    rows = B.jsonl(ctx["place_dir"] / "land.jsonl") if ctx.get("place_dir") else []
    rows = ctx.get("land_rows", rows)
    _, steps = ground(ctx)
    world = {(c["x"], c["y"]): B.cell_steps(c) for c in ctx["facts"]["cells"] if c.get("deltas")}
    for r in rows:
        cx, cy = r["cell"]
        for row, col, dz in r["verts"]:
            want = round(world[(cx, cy)][int(row), int(col)] + dz / 8.0)
            got = steps[(cx, cy)][int(row), int(col)]
            if abs(got - want) > 0.5:
                bad.append(f"land {cx},{cy} [{row},{col}]: built {got * 8:.0f}, land.jsonl wants {want * 8:.0f}")
    built = {(L["x"], L["y"]) for L in ctx["dump"]["land"] if L.get("x") is not None}
    for (cx, cy) in built:
        s = steps[(cx, cy)]
        for (dx, dy), mine_edge, their_edge in (((1, 0), (slice(None), 32), (slice(None), 0)), ((-1, 0), (slice(None), 0), (slice(None), 32)),
                                                ((0, 1), (32, slice(None)), (0, slice(None))), ((0, -1), (0, slice(None)), (32, slice(None)))):
            o = steps.get((cx + dx, cy + dy))
            if o is not None and not np.array_equal(s[mine_edge], o[their_edge]):
                bad.append(f"land {cx},{cy}: tears at the seam with {cx + dx},{cy + dy} ({int(np.abs(s[mine_edge] - o[their_edge]).max() * 8)} units)")
    del quantize
    return bad


def check_clear(ctx) -> list[str]:
    bad = []
    over = {o["fk"]: o for o in ctx["dump"]["overrides"]}
    cleared = set()
    for c in ctx["plan"]["clear"]:
        o = over.get(c["fk"])
        cleared.add(c["fk"])
        if o is None or not (int(o["flags"]) & 0x800):
            bad.append(f"cleared plant {c['fk']} is still enabled")
    m = mine(ctx)
    buildings = [r for r in m["refs"].values() if m["rows"].get(r["fk"], {}).get("kind") in ("building", "static") and r["space"] == "exterior"]
    doors = [r for r in m["refs"].values() if r.get("door") and r["space"] == "exterior"]
    paths = ctx.get("paths") if "paths" in ctx else (B.jsonl(ctx["place_dir"] / "paths.jsonl") if ctx.get("place_dir") else [])
    for cell in ctx["facts"]["cells"]:
        for w in cell.get("refs", []):
            if w["fk"] in cleared or int(w.get("flags", 0)) & 0x800 or not (w.get("base_type") in PLANT_TYPES or w.get("plant") is True):  # a plant by its kind, never by default
                continue
            p = w.get("pos")
            if p is None:
                continue
            why = None
            if any(obb_contains(b, p, 1.0) for b in buildings):
                why = "in a building"
            elif any(math.dist(p[:2], d["pos"][:2]) < PLANT_DOOR_CLEAR for d in doors):
                why = "in a doorway"
            else:
                for pa in paths:
                    pts = pa["points"]
                    if any(point_seg(p, a, b) < float(pa.get("width", 256)) / 2 for a, b in zip(pts[:-1], pts[1:])):
                        why = f"on path {pa['id']}"
                        break
            if why:
                bad.append(f"world plant {w['fk']} ({w['base']}) stands {why}")
    return bad


RENT_ROOM_FACTION, RENT_WI = "Skyrim.esm:09CC97", "Skyrim.esm:035D64"
RENT_INN_RANKS = {RENT_ROOM_FACTION: -1, "Skyrim.esm:05091B": 0, "Skyrim.esm:051596": 0}  # an innkeeper's factions, as Dagur's
_CMP = {"EqualTo": lambda a, b: a == b, "NotEqualTo": lambda a, b: a != b, "GreaterThan": lambda a, b: a > b,
        "GreaterThanOrEqualTo": lambda a, b: a >= b, "LessThan": lambda a, b: a < b, "LessThanOrEqualTo": lambda a, b: a <= b}


def rent_offer_verdicts(npc: dict, offer: list[dict]) -> list[tuple[str, str]]:
    """Each condition of vanilla's rent offer INFO (Skyrim.esm:079B1A, read into dump["rent_offer"]) against this
    actor base's records: (the condition in words, "ok" | "FAIL" | "runtime: why" | "not evaluated: why"). Conditions on
    the actor are decided from the base's factions, ranks and ids; what only the running game knows (the player's gold,
    an actor value) is named, never guessed."""
    ranks = {f["faction"]: f["rank"] for f in npc.get("faction_ranks") or []}
    out = []
    for c in offer:
        fn, op, want = c.get("fn", "?"), c.get("op", "EqualTo"), c.get("value")
        text = f"{fn} {c.get('faction') or c.get('actor_value') or c.get('item') or c.get('object') or ''} {op} {want} ({c.get('run_on')})"
        if c.get("run_on") != "Subject":
            out.append((text, f"runtime: {c.get('run_on')} is the player or a reference, not this actor's records"))
        elif fn == "GetInFaction" and isinstance(want, (int, float)):
            out.append((text, "ok" if _CMP[op](1 if c["faction"] in ranks else 0, want) else "FAIL"))
        elif fn == "GetFactionRank" and isinstance(want, (int, float)):
            out.append((text, "ok" if _CMP[op](ranks.get(c["faction"], -1), want) else "FAIL"))
        elif fn == "GetIsID" and isinstance(want, (int, float)):
            out.append((text, "ok" if _CMP[op](1 if c["object"] in (npc["fk"], npc.get("template")) else 0, want) else "FAIL"))
        elif fn == "GetActorValue":
            out.append((text, "runtime: an actor value is set by scripts; a new base starts at its source's value"))
        else:
            out.append((text, f"not evaluated: {fn} is not one the check knows"))
    return out


def inn_room_problems(npc: dict, m: dict, facts: dict, dump: dict) -> list[str]:
    """What one innkeeper lacks to rent a room the vanilla way (empty: nothing)."""
    bad = []
    ranks = {f["faction"]: f["rank"] for f in npc.get("faction_ranks") or []}
    for fa, want in RENT_INN_RANKS.items():
        if ranks.get(fa) != want:
            bad.append(f"{fa} at rank {want} (has {ranks.get(fa)})")
    if npc.get("voice") not in (dump.get("rent_voices") or []):
        bad.append(f"a voice of form list Skyrim.esm:03B4A5 (has {npc.get('voice')})")
    script = next((s for s in npc.get("scripts") or [] if s["name"] == "RentRoomScript"), None)
    props = {p["name"]: p.get("value") for p in (script or {}).get("props", [])}
    if script is None:
        bad.append("RentRoomScript")
    else:
        bed = m["refs"].get(props.get("Bed"))
        if not (bed and bed.get("base_type") == "FURN" and bed.get("owner") in facts and facts[bed["owner"]].get("vendor")
                and bed["owner"] in npc.get("faction_keys", [])):
            bad.append(f"RentRoomScript Bed {props.get('Bed')} a FURN ref of ours owned by this innkeeper's vendor faction")
        if props.get("WI") != RENT_WI:
            bad.append(f"RentRoomScript WI {RENT_WI} (has {props.get('WI')})")
    bad += [f"rent offer 079B1A: {t}" for t, v in rent_offer_verdicts(npc, dump.get("rent_offer") or []) if v == "FAIL"]
    return bad


SHRINE_SCRIPT = "TempleBlessingScript"
SHRINE_SECONDS = 28800  # eight hours, as vanilla's blessings


def shrine_problems(ctx: dict, m: dict) -> list[str]:
    """What the place's Hist shrine lacks to bless the vanilla way (empty: nothing). A ref of ours whose base is an
    activator of ours carrying TempleBlessingScript with TempleBlessing a spell of ours (Resist Disease for eight hours at one
    fixed magnitude), BlessingMessage a message of ours with text, and AltarRemoveMsg set."""
    dump = ctx["dump"]
    acts = {a["fk"]: a for a in dump.get("activators") or []}
    spells = {s["fk"]: s for s in dump.get("spells") or []}
    msgs = {x["fk"]: x for x in dump.get("messages") or []}
    shrines = [r for r in m["refs"].values() if r.get("base") in acts]
    if not shrines:
        return ["no shrine ref: the draft must add one where the source town's shrine or Hist stands"]
    tried = []
    for r in shrines:
        bad = []
        sc = next((x for x in acts[r["base"]].get("scripts") or [] if x["name"] == SHRINE_SCRIPT), None)
        props = {p["name"]: p.get("value") for p in (sc or {}).get("props", [])}
        if sc is None:
            bad.append(f"base {acts[r['base']].get('edid')} has no {SHRINE_SCRIPT}")
        else:
            sp = spells.get(props.get("TempleBlessing") or "")
            if sp is None:
                bad.append(f"TempleBlessing {props.get('TempleBlessing')} is not a spell of ours")
            else:
                eff = [e for e in sp["effects"] if e.get("actor_value") == "ResistDisease"]
                if not eff:
                    bad.append(f"{sp.get('edid')} has no Resist Disease effect")
                elif not all(e.get("duration") == SHRINE_SECONDS and (e.get("magnitude") or 0) > 0 for e in eff):
                    bad.append(f"{sp.get('edid')}: Resist Disease must last {SHRINE_SECONDS} s at a fixed magnitude above 0 "
                               f"(has {[(e.get('magnitude'), e.get('duration')) for e in eff]})")
            msg = msgs.get(props.get("BlessingMessage") or "")
            if msg is None or not (msg.get("text") or "").strip():
                bad.append(f"BlessingMessage {props.get('BlessingMessage')} is not a message of ours with text")
            if not props.get("AltarRemoveMsg"):
                bad.append("AltarRemoveMsg is not set")
        if not bad:
            return []
        tried.append(f"{m['rows'].get(r['fk'], {}).get('id', r['fk'])}: " + "; ".join(bad))
    return ["the shrine lacks " + " | ".join(tried)]


BOAT_SCRIPT, BOAT_GOLD = "TIF_ARG_BoatTravel", "Skyrim.esm:00000F"
BOAT_PEX = B.ROOT / "out" / "gpu" / "papyrus" / "TIF_ARG_BoatTravel.pex"
WARNINGS: list[str] = []  # what a check notes without failing; main prints them


def boat_problems(ctx: dict, m: dict, facts: dict, npcs: list[dict], detail: str) -> list[str]:
    """What a place's boatman lacks to take the player where the give promises (empty: nothing). A placed person of ours
    in a boatman faction of ours; for every promised destination an INFO on that faction (subject in it, the player holding
    the fare in gold) whose script is TIF_ARG_BoatTravel with Destination a map marker of that place in the world ESM,
    Fare a fixed whole number above 0 matching the gold condition, Gold001 set, and the fragment Fragment_0."""
    dump = ctx["dump"]
    markers = dump.get("world_markers") or {}
    places = ctx.get("places") or B.jsonl(B.DB / "place.jsonl")
    by_name = {}
    for r in places:
        for key in (r.get("name"), r.get("map_label")):
            if key:
                by_name.setdefault(key.casefold(), r)
    names = B.boat_destinations(detail)
    if not names:
        return [f"the give names no destination ({detail!r})"]
    boat = [(n, [f for f in n["faction_keys"] if "Boatman" in (facts.get(f, {}).get("edid") or "") and f.startswith(B.PLUGIN + ":")]) for n in npcs]
    boat = [(n, fs) for n, fs in boat if fs]
    if not boat:
        return ["no person of ours in a boatman faction of ours"]
    infos = [i for t in dump.get("topics") or [] for i in t.get("infos") or []]
    tried = []
    for n, fs in boat:
        bad = []
        for name in names:
            row = by_name.get(name.casefold())
            if row is None:
                bad.append(f"{name}: no place of that name in the database")
                continue
            want = "ANW_MapMarker_" + row["id"].replace("-", "_")
            mine_ = [i for i in infos if any(c.get("fn") == "GetInFaction" and c.get("faction") in fs and c.get("run_on") == "Subject"
                                             and c.get("op") == "EqualTo" and c.get("value") == 1 for c in i.get("conditions") or [])
                     and any(sc["name"] == BOAT_SCRIPT for sc in i.get("scripts") or [])]
            hit = [i for i in mine_ if markers.get(next((p["value"] for sc in i["scripts"] for p in sc["props"] if p["name"] == "Destination"), None)) == want]
            if not hit:
                bad.append(f"{name}: no INFO of this boatman running {BOAT_SCRIPT} to {want}"
                           + ("" if mine_ else f" (he has no {BOAT_SCRIPT} line at all)"))
                continue
            i = hit[0]
            props = {p["name"]: p["value"] for sc in i["scripts"] for p in sc["props"]}
            fare = props.get("Fare")
            if not (isinstance(fare, int) and fare > 0):
                bad.append(f"{name}: Fare {fare!r} is not a fixed amount above 0")
                continue
            if props.get("Gold001") != BOAT_GOLD:
                bad.append(f"{name}: Gold001 is {props.get('Gold001')!r} (want {BOAT_GOLD})")
            if not any(c.get("fn") == "GetGold" and c.get("run_on") == "Target" and c.get("op") == "GreaterThanOrEqualTo" and c.get("value") == fare
                       or c.get("fn") == "GetItemCount" and c.get("item") == BOAT_GOLD and c.get("op") == "GreaterThanOrEqualTo" and c.get("value") == fare
                       for c in i.get("conditions") or []):
                bad.append(f"{name}: no condition that the player holds {fare} gold")
            fr = i.get("fragment") or {}
            if fr.get("file") != BOAT_SCRIPT or fr.get("on_end") != "Fragment_0":
                bad.append(f"{name}: fragment {fr} is not {BOAT_SCRIPT} OnEnd Fragment_0")
        if not bad:
            if not BOAT_PEX.exists():
                WARNINGS.append(f"{BOAT_PEX} is not compiled: the boat lines do nothing in game until it is")
            return []
        tried.append("; ".join(bad))
    return tried[:1]


def check_services(ctx) -> list[str]:
    bad = []
    m = mine(ctx)
    facts = {f["fk"]: f for f in ctx["dump"]["factions"]}
    classes = {c["fk"]: c for c in ctx["dump"]["classes"]}
    placed_npcs = {a["base"] for a in m["actors"].values()}
    npcs = [n for n in m["npcs"].values() if n["fk"] in placed_npcs]
    for g in ctx["gives"]:
        k = g["give_kind_id"]
        if k in NOT_A_PLACE_SERVICE:
            continue
        ok = False
        if k in TRADE_JOB:
            ok = any(TRADE_JOB[k] in n["factions"] and any(facts.get(f, {}).get("vendor") and facts[f].get("chest") for f in n["faction_keys"]) for n in npcs)
        elif k == "trainer":
            ok = any("JobTrainerFaction" in n["factions"] and classes.get(n["class"], {}).get("teaches") for n in npcs)
        elif k == "inn-room":
            tried = [inn_room_problems(n, m, facts, ctx["dump"]) for n in npcs if "JobInnkeeperFaction" in n["factions"]]
            ok = any(not t for t in tried)
            if not ok:
                bad.append(f"promised {k} ({g.get('detail', '')}): " + ("no innkeeper (JobInnkeeperFaction)" if not tried else "the innkeeper lacks " + "; ".join(tried[0])))
                continue
        elif k in CRAFT_KEYWORD:
            ok = any(CRAFT_KEYWORD[k] in (r.get("keywords") or []) for r in m["refs"].values())
        elif k == "shrine-blessing":
            tried = shrine_problems(ctx, m)
            if tried:
                bad.append(f"promised {k} ({g.get('detail', '')}): " + tried[0])
                continue
            ok = True
        elif k == "carriage-or-boat":
            tried = boat_problems(ctx, m, facts, npcs, g.get("detail", ""))
            if tried:
                bad.append(f"promised {k} ({g.get('detail', '')}): " + tried[0])
                continue
            ok = True
        elif k == "fast-travel":
            ok = any((r.get("base_edid") or "") == "MapMarker" for r in m["refs"].values())
        if not ok:
            bad.append(f"promised {k} ({g.get('detail', '')}): nobody and nothing gives it")
    return bad


def is_nordic(model: str | None, edid: str | None) -> bool:
    return bool((model and NORDIC_MODEL.search(model)) or (edid and NORDIC_EDID.match(edid)))


def check_nordic(ctx) -> list[str]:
    m = mine(ctx)
    bad = []
    for r in m["refs"].values():
        if r.get("base_type") in ("STAT", "MSTT", "DOOR", "FURN", "CONT", "ACTI", "LIGH", "TREE", "FLOR", "MISC") and is_nordic(r.get("model"), r.get("base_edid")):
            bad.append(f"{m['rows'].get(r['fk'], {}).get('id', r['fk'])}: Nordic base {r.get('base_edid')} ({r.get('model')})")
    return bad


def check_levelled(ctx) -> list[str]:
    return [f"levelled: {x}" for x in ctx["dump"]["levelled"]]


CHECKS = {"plugin": check_plugin, "seat": check_seat, "overlap": check_overlap, "doors": check_doors, "people": check_people,
          "navmesh": check_navmesh, "land": check_land, "clear": check_clear, "services": check_services,
          "nordic": check_nordic, "levelled": check_levelled}


def run(ctx: dict) -> dict[str, list[str]]:
    return {name: fn(ctx) for name, fn in CHECKS.items()}


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="python -m tools.places check")
    ap.add_argument("place_id")
    ap.add_argument("--out", default=str(B.OUT))
    ap.add_argument("--places-dir", default=str(B.PLACES))
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    t0 = time.time()
    ctx = load(a.place_id, Path(a.out))
    ctx["place_dir"] = Path(a.places_dir) / a.place_id
    res = run(ctx)
    counts = ctx["dump"]["counts"]
    report = {"place_id": a.place_id, "check_s": round(time.time() - t0, 1), "masters": ctx["dump"]["masters"], "counts": counts,
              "results": {k: {"ok": not v, "failures": v[:50], "n": len(v)} for k, v in res.items()}}
    shard = Path(a.out) / "shards" / a.place_id
    (shard / "check.json").write_text(json.dumps(report, indent=1, sort_keys=True) + "\n")
    # the full lists, never cut, one file per check, so nothing is hidden
    full = shard / "check_failures"
    full.mkdir(parents=True, exist_ok=True)
    for k, v in res.items():
        (full / f"{k}.txt").write_text("".join(f"{f}\n" for f in v))
    if a.json:
        print(json.dumps(report, sort_keys=True))
    else:
        for w in WARNINGS:
            print(f"warn {w}")
        for k, v in res.items():
            print(f"{'ok  ' if not v else 'FAIL'} {k}" + ("" if not v else f" ({len(v)})"))
            for f in v[:20]:
                print(f"     {f}")
        print(f"check {a.place_id}: {sum(1 for v in res.values() if not v)}/{len(res)} green in {report['check_s']} s")
    return 0 if not any(res.values()) else 1
