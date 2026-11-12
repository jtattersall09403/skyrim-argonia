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
KEEP = {b"NPC_", b"LVLN", b"ECZN", b"RACE", b"CELL", b"WRLD", b"FLOR", b"TREE"}
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
         "world": {}}
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


def pct(v, ps=(10, 50, 90)):
    return [round(float(np.percentile(v, p)), 2) for p in ps] if len(v) else []


def cell_of(x, y):
    return (int(x // CELL), int(y // CELL))


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
    kinds_cell = defaultdict(set)
    harvest_total = {"FLOR": 0, "TREE": 0}
    kinds_all = set()
    for fid, x, y, _, _ in o["refr"]:
        for sig, tbl in (("FLOR", o["flor"]), ("TREE", o["tree"])):
            if fid in tbl and tbl[fid][1]:
                xy = cell_of(x, y)
                if xy in cls:
                    harvest[xy] += 1
                    kinds_cell[xy].add(tbl[fid][1])
                    kinds_all.add(tbl[fid][1])
                    harvest_total[sig] += 1
    hcls = Counter()
    for xy, k in harvest.items():
        hcls[cls[xy]] += k
    kcls = defaultdict(list)
    for xy in cls:
        kcls[cls[xy]].append(len(kinds_cell.get(xy, ())))
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
            "distinct_kinds_per_cell_p10_50_90_by_class": {k: pct(v) for k, v in kcls.items()},
            "distinct_kinds_per_cell_mean_by_class": {k: round(float(np.mean(v)), 3) for k, v in kcls.items()},
            "method": "REFR in Tamriel whose base is a FLOR or TREE record with a PFIG (the ingredient it yields); "
                      "cell from the ref's position; a kind is a distinct PFIG form; per-cell figures divide by all "
                      "cells of the class including cells with none; near water = water plus shore classes"},
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
