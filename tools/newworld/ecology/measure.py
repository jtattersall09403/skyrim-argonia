"""How Skyrim.esm ecology is placed in Tamriel (decision 0034): creature ACHR density by habitat, levelled share,
group sizes, hostile share, distance to doors and named cells, harvestable REFR density, encounter zones.
Writes newworld/sources/ecology/skyrim_measures.json (numbers only; nothing from the game is committed, 0003).

    python3 -m tools.newworld.ecology.measure [--out path]

Reads Skyrim.esm (Data dir: $ARGONIA_GAME_ROOT/Data or ~/games/skyrimse/Data) in one pass. Needs numpy.
Habitat class per Tamriel exterior cell with LAND (the old creature measurement's rule): water = over half the 33x33
vertices under the cell's water height (XCLW, else the world default); shore = some under; mountain = mean ground
over 4000 units and no water; forest = 10 or more TREE refs in the cell; open = the rest.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import struct
import zlib
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

TAMRIEL = 0x3C
CELL = 4096
M = 70.03
HUMANOID = ("Nord", "Imperial", "Breton", "Redguard", "HighElf", "DarkElf", "WoodElf", "Orc", "Argonian", "Khajiit",
            "Elder", "Child", "Draugr", "Skeleton", "Falmer", "Dremora", "Vampire", "Afflicted", "Snow", "Manakin",
            "Default", "Naga", "Human", "Elf")
KEEP = {b"NPC_", b"LVLN", b"ECZN", b"RACE", b"CELL", b"WRLD", b"FLOR", b"TREE", b"ACTI"}
CRITTER = re.compile(r"^(critter|DragonFly|Fish|Firefly|Moth|FXbird|FXBird|FXbat|FCAmb)", re.I)
NOT_CRITTER = re.compile(r"Dummy|Trig|Quest|Furniture|Tank|CatchData", re.I)
OUT = Path(__file__).resolve().parents[3] / "newworld" / "sources" / "ecology" / "skyrim_measures.json"
GROUP_R = 1500.0


def data_dir() -> Path:
    root = os.environ.get("ARGONIA_GAME_ROOT")
    return (Path(root) / "Data") if root else Path.home() / "games" / "skyrimse" / "Data"


def subs(body: bytes):
    out, i, big = [], 0, None
    while i + 6 <= len(body):
        sig = body[i:i + 4]
        size = struct.unpack_from("<H", body, i + 4)[0]
        i += 6
        if sig == b"XXXX":
            big = struct.unpack_from("<I", body, i)[0]
            i += size
            continue
        if big is not None:
            size, big = big, None
        out.append((sig, body[i:i + size]))
        i += size
    return out


def _z(b: bytes) -> str:
    return b.split(b"\0", 1)[0].decode("latin1")


def heights(vhgt: bytes) -> np.ndarray:
    off = struct.unpack_from("<f", vhgt)[0]
    d = np.frombuffer(vhgt, np.int8, 1089, 4).reshape(33, 33).astype(np.float64)
    col0 = off + np.cumsum(d[:, 0])
    rows = col0[:, None] + np.concatenate([np.zeros((33, 1)), np.cumsum(d[:, 1:], axis=1)], axis=1)
    return rows * 8


def scan(path: Path) -> dict:
    blob = path.read_bytes()
    o = {"npc": {}, "lvln": {}, "race": {}, "eczn": {}, "cells": {}, "flor": {}, "tree": {}, "achr": [], "refr": [],
         "world": {}, "acti": {}, "navm": set()}
    cur = {"cell": None, "interior": False}

    def body(i, size, flags):
        b = blob[i + 24:i + 24 + size]
        return zlib.decompress(b[4:]) if flags & 0x40000 else b

    def walk(i, end, wrld):
        while i < end:
            sig = blob[i:i + 4]
            size = struct.unpack_from("<I", blob, i + 4)[0]
            if sig == b"GRUP":
                label, gtype = struct.unpack_from("<Ii", blob, i + 8)
                if gtype == 0 and blob[i + 8:i + 12] not in KEEP:
                    i += size
                    continue
                walk(i + 24, i + size, label if gtype == 1 else wrld)
                i += size
                continue
            flags, fid = struct.unpack_from("<II", blob, i + 8)
            if sig == b"NAVM" and wrld == TAMRIEL and cur["cell"] is not None:
                o["navm"].add(cur["cell"])
            if sig in KEEP or (sig in (b"ACHR", b"REFR", b"LAND") and wrld == TAMRIEL):
                sb = subs(body(i, size, flags))
                d = dict(sb)
                if sig == b"NPC_":
                    acbs = d.get(b"ACBS", b"\0" * 24)
                    ai = d.get(b"AIDT", b"\0\0")
                    o["npc"][fid] = {"edid": _z(d.get(b"EDID", b"")),
                                     "race": struct.unpack("<I", d[b"RNAM"])[0] if b"RNAM" in d else None,
                                     "tplt": struct.unpack("<I", d[b"TPLT"])[0] if b"TPLT" in d else None,
                                     "aggr": ai[0], "conf": ai[1], "pcmult": bool(struct.unpack_from("<I", acbs)[0] & 0x80)}
                elif sig == b"LVLN":
                    o["lvln"][fid] = (_z(d.get(b"EDID", b"")),
                                      [struct.unpack_from("<HHIH", b)[2] for s, b in sb if s == b"LVLO" and len(b) >= 10])
                elif sig == b"RACE":
                    o["race"][fid] = _z(d.get(b"EDID", b""))
                elif sig == b"ECZN":
                    dd = d.get(b"DATA", b"")
                    if len(dd) >= 12:
                        _, loc, _, mn, fl, mx = struct.unpack_from("<IIbbBb", dd)
                        o["eczn"][fid] = {"edid": _z(d.get(b"EDID", b"")), "min": mn, "max": mx, "flags": fl}
                elif sig in (b"FLOR", b"TREE"):
                    pf = d.get(b"PFIG")
                    o["flor" if sig == b"FLOR" else "tree"][fid] = (
                        _z(d.get(b"EDID", b"")), struct.unpack("<I", pf)[0] if pf and len(pf) >= 4 else None)
                elif sig == b"ACTI":
                    edid = _z(d.get(b"EDID", b""))
                    if CRITTER.match(edid) and not NOT_CRITTER.search(edid):
                        o["acti"][fid] = (edid, spawn_windows(d.get(b"VMAD")))
                elif sig == b"WRLD" and fid == TAMRIEL and b"DNAM" in d:
                    o["world"]["water"] = struct.unpack_from("<f", d[b"DNAM"], 4)[0]
                elif sig == b"CELL" and wrld == TAMRIEL:
                    if b"XCLC" in d:
                        xy = struct.unpack_from("<ii", d[b"XCLC"])
                        cur["cell"] = xy
                        o["cells"][xy] = {"edid": _z(d.get(b"EDID", b"")),
                                          "water": struct.unpack("<f", d[b"XCLW"])[0] if b"XCLW" in d else None,
                                          "zone": b"XEZN" in d, "h": None}
                    else:
                        cur["cell"] = None
                elif sig == b"LAND" and cur["cell"] is not None and b"VHGT" in d:
                    o["cells"][cur["cell"]]["h"] = heights(d[b"VHGT"])
                elif sig in (b"ACHR", b"REFR") and b"NAME" in d and b"DATA" in d:
                    p = struct.unpack("<3f", d[b"DATA"][:12])
                    row = (struct.unpack("<I", d[b"NAME"])[0], p[0], p[1], b"XTEL" in d,
                           struct.unpack("<I", d[b"XEZN"])[0] if b"XEZN" in d else None)
                    o["achr" if sig == b"ACHR" else "refr"].append(row)
            i += 24 + size

    walk(struct.unpack_from("<I", blob, 4)[0] + 24, len(blob), None)
    return o


def spawn_windows(vmad: bytes | None) -> list:
    """[start hour, end hour, most critters] of each critter spawn script on an activator's VMAD (v5, object format 2)."""
    if not vmad or len(vmad) < 6:
        return []
    out = []
    try:
        _, fmt, n = struct.unpack_from("<hhH", vmad, 0)
        o = 6
        for _ in range(n):
            ln, = struct.unpack_from("<H", vmad, o)
            name = vmad[o + 2:o + 2 + ln].decode("latin1")
            o += 2 + ln + 1
            pc, = struct.unpack_from("<H", vmad, o)
            o += 2
            props = {}
            for _ in range(pc):
                ln, = struct.unpack_from("<H", vmad, o)
                pn = vmad[o + 2:o + 2 + ln].decode("latin1")
                t = vmad[o + 2 + ln]
                o += 4 + ln
                if t == 1:
                    o += 8
                elif t == 2:
                    ln, = struct.unpack_from("<H", vmad, o)
                    o += 2 + ln
                elif t in (3, 4):
                    props[pn] = struct.unpack_from("<i" if t == 3 else "<f", vmad, o)[0]
                    o += 4
                elif t == 5:
                    props[pn] = vmad[o]
                    o += 1
                else:
                    return out
            if name.lower().startswith("critterspawn") and "fStartSpawnTime" in props:
                out.append([round(props["fStartSpawnTime"], 1), round(props["fEndSpawnTime"], 1), int(props.get("iMaxCritterCount", 0))])
    except (struct.error, KeyError):
        pass
    return out


def pct(v, ps=(10, 50, 90)):
    return [round(float(np.percentile(v, p)), 2) for p in ps] if len(v) else []


def cell_of(x, y):
    return (int(x // CELL), int(y // CELL))


def black_marsh_critters(_o: dict, skyrim_per_cell: float) -> dict:
    """How the modder of this world's own ground places spawners: King of the Murkmire's critter spawner refs (its own
    and Skyrim's bases) against the cells its refs stand in, and that per cell over Skyrim's per land cell. Black Marsh
    itself and Tropical Skyrim place none."""
    from tools.argonia_world.esm import Plugin
    from tools.newworld.ecology.census import plugin_path
    p = Plugin.read(plugin_path("King of the Murkmire.esp"), {"ACTI", "REFR", "CELL"})
    own = {r.key: r.edid for r in p.records("ACTI") if r.edid}
    spawn = re.compile(r"^(critterSpawn|ArgoniaCritterSpawn)", re.I)
    base = {r.key: r.edid for r in Plugin.read(data_dir() / "Skyrim.esm", {"ACTI"}).records("ACTI") if r.edid}
    cells, n, in_cells = set(), 0, set()
    for r in p.records("REFR"):
        d = r.sub("DATA")
        if not d or len(d) < 12:
            continue
        x, y = struct.unpack_from("<2f", d)
        cells.add(cell_of(x, y))
        e = own.get(r.ref("NAME")) or base.get(r.ref("NAME"))
        if e and spawn.match(e):
            n += 1
            in_cells.add(cell_of(x, y))
    per = n / len(cells)
    return {"plugin": "King of the Murkmire.esp", "spawner_refs": n, "cells_with_refs": len(cells), "cells_with_spawners": len(in_cells),
            "spawners_per_cell": round(per, 3), "skyrim_spawners_per_land_cell": round(skyrim_per_cell, 3),
            "factor": round(per / skyrim_per_cell, 1),
            "method": "REFR of the plugin placed by x, y into 4096-unit cells; the cells counted are those holding any ref of "
                      "it; spawners are bases named critterSpawn* or ArgoniaCritterSpawn*"}


def measure_critters(o: dict, cls: dict, cells: dict, world_water: float, land: Counter) -> dict:
    """Skyrim's critter spawn activators (insects, fish, birds) placed in Tamriel: per base the refs per 100 cells of
    each class, where they stand against the water (over it, on its edge within 2 m, dry), how many stand within 15 m
    of a harvestable plant, and the hours the base's spawn script runs."""
    flor = np.array([(x, y) for fid, x, y, _, _ in o["refr"] if fid in o["flor"] and o["flor"][fid][1]])
    rows: dict = defaultdict(Counter)
    for fid, x, y, _, _ in o["refr"]:
        if fid not in o["acti"]:
            continue
        xy = cell_of(x, y)
        if xy not in cls:
            continue
        c = cells[xy]
        wl = c["water"] if c["water"] is not None and c["water"] < 1e6 else world_water
        i, j = min(32, max(0, int((x - xy[0] * CELL) / 128))), min(32, max(0, int((y - xy[1] * CELL) / 128)))
        z = float(c["h"][j, i]) - wl
        r = rows[o["acti"][fid][0]]
        r["n"] += 1
        r["class:" + cls[xy]] += 1
        r["water:" + ("over" if z < 0 else "edge" if z < 140 else "dry")] += 1
        r["flora"] += int(len(flor) > 0 and float(np.sqrt(((flor - (x, y)) ** 2).sum(1)).min()) / M < 15)
    bases = {}
    for fid, (edid, win) in sorted(o["acti"].items(), key=lambda kv: kv[1][0]):
        r = rows.get(edid)
        if not r:
            continue
        n = r["n"]
        bases[edid] = {"refs": n, "refs_per_100_cells_by_class": {k: round(100 * r["class:" + k] / land[k], 3) for k in land if r["class:" + k]},
                       "share_over_water": round(r["water:over"] / n, 3), "share_on_water_edge": round(r["water:edge"] / n, 3),
                       "share_dry": round(r["water:dry"] / n, 3), "share_near_harvestable_15m": round(r["flora"] / n, 3),
                       "spawn_hours": win}
    spawners = re.compile(r"^(critterSpawn|ArgoniaCritterSpawn)", re.I)
    sky = sum(r["n"] for e, r in rows.items() if spawners.match(e))
    return {"bases": bases, "black_marsh": black_marsh_critters(o, sky / sum(land.values())),
            "method": "REFR in Tamriel whose base ACTI is a critter spawner or critter (editor id starting critter, DragonFly, "
                      "Fish, Firefly, Moth, FXbird, FXbat, FCAmb; not dummies, triggers, furniture or tanks), in a cell with LAND; "
                      "per 100 cells = refs / cells of the class * 100; over water = ground under the cell's water height "
                      "at the ref, on the edge = within 2 m above it; near a harvestable = a FLOR with an ingredient within "
                      "15 m; spawn_hours = the start and end hour and most critters of each critterspawn script of the base"}


def measure_wild(o: dict, cls: dict, rows: list) -> dict:
    """Skyrim's density where the player walks: per 100 cells of each class among the Tamriel cells that carry a
    navmesh (the playable land; the LAND beyond the border has none), the creature refs split by temper (benign:
    every resolved record's aggression 0; hostile: any above) and the critter spawner refs (ACTI critters)."""
    nav = {xy: cls[xy] for xy in o["navm"] if xy in cls}
    land = Counter(nav.values())
    benign, hostile, crit = Counter(), Counter(), Counter()
    for r in rows:
        if r["cell"] in nav:
            (hostile if r["hostile"] else benign)[nav[r["cell"]]] += 1
    for fid, x, y, _, _ in o["refr"]:
        if fid in o["acti"] and cell_of(x, y) in nav:
            crit[nav[cell_of(x, y)]] += 1

    def per100(c):
        return {k: round(100 * c[k] / land[k], 2) for k in sorted(land)}

    n = sum(land.values())
    return {"navmesh_cells": n, "by_class": dict(sorted(land.items())),
            "benign_per_100_cells_by_class": per100(benign), "hostile_per_100_cells_by_class": per100(hostile),
            "critters_per_100_cells_by_class": per100(crit),
            "benign_per_100_cells_all": round(100 * sum(benign.values()) / n, 2),
            "hostile_per_100_cells_all": round(100 * sum(hostile.values()) / n, 2),
            "critters_per_100_cells_all": round(100 * sum(crit.values()) / n, 2),
            "method": "Tamriel exterior cells holding a NAVM record (Skyrim navmeshes only the land the player can walk); "
                      "classes and creature rows as creature_density; critters as the critters section's bases"}


def measure(o: dict) -> dict:
    cells, world_water = o["cells"], o["world"]["water"]
    trees = Counter()
    for fid, x, y, _, _ in o["refr"]:
        if fid in o["tree"]:
            trees[cell_of(x, y)] += 1

    def klass(xy):
        c = cells[xy]
        if c["h"] is None:
            return None
        wl = c["water"] if c["water"] is not None and c["water"] < 1e6 else world_water
        wet = float((c["h"] < wl).mean())
        if wet > 0.5:
            return "water"
        if wet > 0:
            return "shore"
        if float(c["h"].mean()) > 4000:
            return "mountain"
        return "forest" if trees[xy] >= 10 else "open"

    cls = {xy: klass(xy) for xy in cells}
    cls = {k: v for k, v in cls.items() if v}
    land = Counter(cls.values())
    n_land = len(cls)

    def per100(counter):
        return {k: round(100 * counter[k] / land[k], 2) for k in land}

    # creatures
    def is_creature_race(rid):
        r = o["race"].get(rid, "")
        return bool(r) and not any(h.lower() in r.lower() for h in HUMANOID)

    def resolve(fid, seen=()):
        if fid in o["npc"]:
            n = o["npc"][fid]
            if n["tplt"] in o["lvln"] or n["tplt"] in o["npc"]:
                return resolve(n["tplt"], seen) or [fid]
            return [fid]
        if fid in o["lvln"] and fid not in seen:
            out = []
            for f in o["lvln"][fid][1]:
                out += resolve(f, seen + (fid,))
            return out
        return []

    rows = []
    for fid, x, y, door, zone in o["achr"]:
        kids = [k for k in resolve(fid) if k in o["npc"]]
        if not kids or not any(is_creature_race(o["npc"][k]["race"]) for k in kids):
            continue
        n = o["npc"].get(fid)
        levelled = fid in o["lvln"] or bool(n and n["tplt"] in o["lvln"])
        races = Counter(o["race"].get(o["npc"][k]["race"], "?") for k in kids)
        xy = cell_of(x, y)
        rows.append({"x": x, "y": y, "cell": xy, "cls": cls.get(xy), "lev": levelled,
                     "hostile": max(o["npc"][k]["aggr"] for k in kids) >= 1, "race": races.most_common(1)[0][0],
                     "zone": zone})
    rows = [r for r in rows if r["cls"]]  # inside LAND cells (Tamriel exterior)
    cr = Counter(r["cls"] for r in rows)
    occupied = Counter(cls[c] for c in {r["cell"] for r in rows})
    # groups: connected components of creature refs within GROUP_R units
    pts = np.array([(r["x"], r["y"]) for r in rows])
    grid = defaultdict(list)
    for i, (x, y) in enumerate(pts):
        grid[(int(x // GROUP_R), int(y // GROUP_R))].append(i)
    parent = list(range(len(pts)))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for (gx, gy), ids in grid.items():
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for j in grid.get((gx + dx, gy + dy), ()):
                    for i in ids:
                        if i < j and (pts[i] - pts[j]) @ (pts[i] - pts[j]) <= GROUP_R ** 2:
                            parent[find(i)] = find(j)
    sizes = Counter(Counter(find(i) for i in range(len(pts))).values())
    n_groups = sum(sizes.values())
    # nearest door (XTEL) and named cell
    doors = np.array([(x, y) for fid, x, y, dr, _ in o["refr"] if dr])
    named = np.array([((x + .5) * CELL, (y + .5) * CELL) for (x, y), c in cells.items() if c["edid"]])

    def nearest(src, tgt):
        out = []
        for i in range(0, len(src), 500):
            d = ((src[i:i + 500, None, :] - tgt[None]) ** 2).sum(2)
            out.append(np.sqrt(d.min(1)))
        return np.concatenate(out) / M

    dm, nm = nearest(pts, doors), nearest(pts, named)
    # harvestables
    harvest = Counter()
    base_cls = defaultdict(Counter)       # class -> base editor id -> refs
    kinds_cell = defaultdict(set)
    harvest_total = {"FLOR": 0, "TREE": 0}
    kinds_all = set()
    for fid, x, y, _, _ in o["refr"]:
        for sig, tbl in (("FLOR", o["flor"]), ("TREE", o["tree"])):
            if fid in tbl and tbl[fid][1]:
                xy = cell_of(x, y)
                if xy in cls:
                    harvest[xy] += 1
                    base_cls[cls[xy]][tbl[fid][0]] += 1
                    kinds_cell[xy].add(tbl[fid][1])
                    kinds_all.add(tbl[fid][1])
                    harvest_total[sig] += 1
    hcls = Counter()
    for xy, k in harvest.items():
        hcls[cls[xy]] += k
    kcls = defaultdict(list)
    for xy in cls:
        kcls[cls[xy]].append(len(kinds_cell.get(xy, ())))
    critters = measure_critters(o, cls, cells, world_water, land)
    wild = measure_wild(o, cls, rows)
    ez = o["eczn"]
    cell_zone = [xy for xy, c in cells.items() if c["zone"]]
    return {
        "source": "Skyrim.esm (Update.esm overrides not applied), Tamriel exterior cells with LAND",
        "cells": {
            "tamriel_exterior_cells": len(cells), "with_land": n_land, "by_class": dict(land),
            "method": "classes as in the module docstring: water (>50% vertices under water), shore (some), "
                      "mountain (mean ground > 4000 units, dry), forest (>=10 TREE refs), open (rest)"},
        "creature_density": {
            "creature_refs": len(rows), "refs_by_class": dict(cr),
            "refs_per_100_cells_by_class": per100(cr),
            "refs_per_100_cells_all": round(100 * len(rows) / n_land, 2),
            "occupied_cells_by_class": dict(occupied),
            "levelled_share": round(sum(r["lev"] for r in rows) / len(rows), 3),
            "levelled_share_by_class": {k: round(sum(r["lev"] for r in rows if r["cls"] == k) / cr[k], 3) for k in cr},
            "group_size_distribution": {"groups": n_groups, "by_size": {str(k): v for k, v in sorted(sizes.items())},
                                        "mean": round(len(rows) / n_groups, 2),
                                        "share_of_groups_size_1": round(sizes[1] / n_groups, 3),
                                        "share_of_groups_size_2_to_3": round((sizes[2] + sizes[3]) / n_groups, 3),
                                        "share_of_groups_size_4_plus": round(sum(v for k, v in sizes.items() if k >= 4) / n_groups, 3)},
            "hostile_share": round(sum(r["hostile"] for r in rows) / len(rows), 3),
            "hostile_share_by_class": {k: round(sum(r["hostile"] for r in rows if r["cls"] == k) / cr[k], 3) for k in cr},
            "races_top": dict(Counter(r["race"] for r in rows).most_common(25)),
            "nearest_door_m_p10_50_90": pct(dm), "within_60m_of_a_door": round(float((dm < 60).mean()), 3),
            "nearest_named_cell_m_p10_50_90": pct(nm),
            "within_200m_of_a_named_cell": round(float((nm < 200).mean()), 3),
            "method": "ACHR in Tamriel whose base NPC_ (or every NPC_ an LVLN base or templated list can resolve to) has "
                      "a race editor-ID with none of the humanoid words (Nord, Imperial, ..., Draugr, Skeleton, Falmer, "
                      "Dremora, Vampire, Afflicted, Snow, Manakin, Default, Naga, Human, Elf); cell from the ref's "
                      "position; per 100 cells = refs / cells of that class * 100; levelled = base is an LVLN or an "
                      "NPC_ templated to one; group = connected refs each within 1500 units of another (single-link, "
                      "all classes); hostile = any resolved NPC_ with AIDT aggression >= 1 (race and faction names are "
                      "not read, aggression is the engine's own flag); distance = ref to nearest door/cave mouth "
                      "(REFR with XTEL) and to the centre of the nearest named exterior cell (cell editor-ID); "
                      "Skyrim has no road records (its roads are painted), so road distance is not measured here "
                      "(see tools.newworld.roads for the new world's own roads)"},
        "harvestable_density": {
            "harvestable_refs": sum(harvest_total.values()), "flor_refs": harvest_total["FLOR"],
            "tree_refs": harvest_total["TREE"], "distinct_ingredient_kinds_total": len(kinds_all),
            "refs_per_cell_by_class": {k: round(hcls[k] / land[k], 3) for k in land},
            "refs_per_100_cells_by_class": per100(hcls),
            "refs_per_100_cells_near_water_shore_or_water": round(100 * (hcls["water"] + hcls["shore"]) / (land["water"] + land["shore"]), 1),
            "refs_per_100_cells_forest": round(100 * hcls["forest"] / land["forest"], 1),
            "refs_per_100_cells_open": round(100 * hcls["open"] / land["open"], 1),
            "bases_by_class_top": {k: dict(c.most_common(25)) for k, c in sorted(base_cls.items())},
            "distinct_kinds_per_cell_p10_50_90_by_class": {k: pct(v) for k, v in kcls.items()},
            "distinct_kinds_per_cell_mean_by_class": {k: round(float(np.mean(v)), 3) for k, v in kcls.items()},
            "method": "REFR in Tamriel whose base is a FLOR or TREE record with a PFIG (the ingredient it yields); "
                      "cell from the ref's position; a kind is a distinct PFIG form; per-cell figures divide by all "
                      "cells of the class including cells with none; near water = water plus shore classes"},
        "critters": critters,
        "wild": wild,
        "encounter_zones": {
            "eczn_records": len(ez),
            "min_level_min_max": [min(z["min"] for z in ez.values()), max(z["min"] for z in ez.values())],
            "max_level_min_max": [min(z["max"] for z in ez.values()), max(z["max"] for z in ez.values())],
            "max_level_zero_share": round(sum(z["max"] == 0 for z in ez.values()) / len(ez), 3),
            "min_level_counts_top": {str(k): v for k, v in Counter(z["min"] for z in ez.values()).most_common(12)},
            "never_resets": sum(1 for z in ez.values() if z["flags"] & 1),
            "match_pc_below_min": sum(1 for z in ez.values() if z["flags"] & 2),
            "tamriel_exterior_cells_with_zone": len(cell_zone),
            "share_of_tamriel_exterior_cells_with_zone": round(len(cell_zone) / len(cells), 3),
            "creature_refs_with_zone_ref": sum(1 for r in rows if r["zone"]),
            "method": "ECZN DATA (location, rank, min level, flags, max level; max 0 = no cap); cells counted when the "
                      "Tamriel exterior CELL record carries XEZN; per-ref XEZN on creature ACHR counted apart "
                      "(most creature refs inherit the cell's or location's zone)"},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args()
    res = measure(scan(data_dir() / "Skyrim.esm"))
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps({k: res[k] for k in ("creature_density", "harvestable_density", "encounter_zones")}, indent=1)[:3000])


if __name__ == "__main__":
    main()
