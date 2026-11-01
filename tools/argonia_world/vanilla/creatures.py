"""How Skyrim.esm places its wilderness creatures (1.15 §g.1, decision 0034): the spawn refs in Tamriel, the
levelled lists behind them, the encounter zones, density per cell by terrain, nearness to water, doors (dens) and
named cells (places), hostile against passive. Prints JSON; the numbers are in the creatures lane report.

    python3 -m tools.argonia_world.vanilla.creatures [--json out/creatures/vanilla.json]

Terrain class per cell (from the LAND and the cell's water; Tamriel's default water when none):
    water     more than half the vertices under the water
    shore     some vertices under the water
    mountain  mean ground over 4,000 units (~57 m; Skyrim's tree line is near 6,000) and no water
    forest    10 or more TREE refs (the vegetation lane's forested-cell cut)
    open      the rest
"""
from __future__ import annotations

import argparse
import json
import pickle
from collections import Counter
from pathlib import Path

import numpy as np

from tools.argonia_world.creatures import actors
from tools.argonia_world.skyrim_units import CELL_UNITS, UNITS_PER_METRE
from tools.argonia_world.vanilla import load

ACTORS = Path.home() / ".cache" / "argonia-vanilla" / "actors.pkl"
HUMANOID = ("Nord", "Imperial", "Breton", "Redguard", "HighElf", "DarkElf", "WoodElf", "Orc", "Argonian", "Khajiit",
            "Elder", "Child", "Draugr", "Skeleton", "Falmer", "Dremora", "Vampire", "Afflicted", "Snow", "Manakin")


def scan(rebuild=False) -> actors.Scan:
    if ACTORS.exists() and not rebuild:
        return pickle.loads(ACTORS.read_bytes())
    s = actors.scan(load.data_dir() / "Skyrim.esm")
    ACTORS.parent.mkdir(parents=True, exist_ok=True)
    ACTORS.write_bytes(pickle.dumps(s))
    return s


def is_creature(s, npc_fid) -> bool:
    n = s.npcs[npc_fid]
    r = s.races.get(n.race)
    return r is not None and not any(h.lower() in r.edid.lower() for h in HUMANOID)


def cell_class(t, xy, trees) -> str:
    c = t["cells"].get(xy)
    if c is None or c["h"] is None:
        return "none"
    wl = c["water"] if c["water"] is not None and c["water"] < 1e6 else t["world"]["water"]
    wet = float((c["h"] < wl).mean())
    if wet > 0.5:
        return "water"
    if wet > 0:
        return "shore"
    if float(c["h"].mean()) > 4000:
        return "mountain"
    return "forest" if trees.get(xy, 0) >= 10 else "open"


def measure() -> dict:
    s, t = scan(), load.tamriel()
    tree = {f for f, v in t["forms"].items() if v[0] == "TREE"}
    trees = Counter(r[0] for r in t["refs"] if r[1] in tree)
    doors = np.array([(r[2], r[3]) for r in t["refs"] if r[9]], np.float64)  # XTEL: cave and house mouths
    named = np.array([((x + .5) * CELL_UNITS, (y + .5) * CELL_UNITS) for (x, y), c in t["cells"].items() if c["edid"]])
    cls = {xy: cell_class(t, xy, trees) for xy in t["cells"]}
    land = Counter(cls.values())
    ext = [a for a in s.achrs if a.world == load.TAMRIEL]
    rows = []
    for a in ext:
        kids = actors.resolve(s, a.base)
        kids = [k for k in kids if k in s.npcs]
        if not kids or not any(is_creature(s, k) for k in kids):
            continue
        n = s.npcs[a.base] if a.base in s.npcs else None
        lv = n.template if n and n.template in s.lvlns else (a.base if a.base in s.lvlns else None)
        p = np.array(a.pos[:2])
        dd = float(np.sqrt(((doors - p) ** 2).sum(1)).min()) / UNITS_PER_METRE if len(doors) else -1
        dn = float(np.sqrt(((named - p) ** 2).sum(1)).min()) / UNITS_PER_METRE
        races = Counter(s.races[s.npcs[k].race].edid for k in kids)
        rows.append({"base": n.edid if n else s.lvlns[a.base].edid, "list": s.lvlns[lv].edid if lv else None,
                     "cls": cls.get(a.cell, "none"), "door_m": dd, "named_m": dn, "zone": a.zone,
                     "race": races.most_common(1)[0][0], "hostile": max(s.npcs[k].aggression for k in kids) >= 1,
                     "cell": a.cell})
    per_cls = Counter(r["cls"] for r in rows)
    per_cell = Counter(r["cell"] for r in rows)
    occupied = Counter(cls[c] for c in per_cell if c in cls)
    lists_used = Counter(r["list"] for r in rows if r["list"])
    lv = []
    for e, k in lists_used.most_common(25):
        L = next(x for x in s.lvlns.values() if x.edid == e)
        levels = sorted({x[0] for x in L.entries})
        lv.append({"list": e, "refs": k, "entries": len(L.entries), "levels": levels, "chance_none": L.chance_none,
                   "flags": L.flags})
    all_lists = [x for x in s.lvlns.values() if any(f in s.npcs and is_creature(s, f) for f in actors.resolve(s, x.fid))]
    q = lambda v: [round(float(np.percentile(v, p)), 1) for p in (10, 50, 90)] if v else []
    return {
        "creature_refs": len(rows),
        "levelled_share": round(sum(1 for r in rows if r["list"]) / max(1, len(rows)), 3),
        "cells_by_class": dict(land),
        "refs_by_class": dict(per_cls),
        "refs_per_100_cells_by_class": {k: round(100 * per_cls[k] / land[k], 2) for k in land if land[k]},
        "occupied_cells_by_class": dict(occupied),
        "refs_per_occupied_cell": q(list(per_cell.values())),
        "door_m_p10_50_90": q([r["door_m"] for r in rows]),
        "within_60m_of_a_door": round(sum(r["door_m"] < 60 for r in rows) / max(1, len(rows)), 3),
        "named_cell_m_p10_50_90": q([r["named_m"] for r in rows]),
        "within_200m_of_a_named_cell": round(sum(r["named_m"] < 200 for r in rows) / max(1, len(rows)), 3),
        "hostile_share": round(sum(r["hostile"] for r in rows) / max(1, len(rows)), 3),
        "hostile_by_class": {k: round(sum(r["hostile"] for r in rows if r["cls"] == k) / v, 2) for k, v in per_cls.items()},
        "races": dict(Counter(r["race"] for r in rows).most_common(30)),
        "lists_top": lv,
        "creature_lists": len(all_lists),
        "creature_list_entries_p10_50_90": q([len(x.entries) for x in all_lists]),
        "creature_list_chance_none": dict(Counter(x.chance_none for x in all_lists)),
        "creature_list_levels_distinct_p50": q([len({e[0] for e in x.entries}) for x in all_lists]),
        "eczn": len(s.ecznS),
        "eczn_never_resets": sum(1 for z in s.ecznS.values() if z.flags & 1),
        "eczn_min_level": dict(Counter(z.min_level for z in s.ecznS.values()).most_common(10)),
        "eczn_max_level_zero_share": round(sum(z.max_level == 0 for z in s.ecznS.values()) / len(s.ecznS), 3),
        "eczn_with_location": sum(1 for z in s.ecznS.values() if z.location),
        "exterior_creature_refs_with_zone": sum(1 for r in rows if r["zone"]),
        "exterior_cells_with_zone": len(s.cell_zone),
        "interior_cells_with_zone": len(s.interior_zone),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json")
    a = ap.parse_args(argv)
    m = measure()
    txt = json.dumps(m, indent=1, default=str)
    if a.json:
        Path(a.json).parent.mkdir(parents=True, exist_ok=True)
        Path(a.json).write_text(txt + "\n")
    print(txt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
