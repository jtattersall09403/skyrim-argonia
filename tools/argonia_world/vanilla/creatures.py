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


# -- kinds per region (1.15 round 5, owner #37 2026-11-03: "at least as many kinds per equivalent-sized region") --
# A kind is one species: Skyrim's races collapsed (three bears, two trolls named apart as Skyrim names them, the
# spider sizes, spriggan and matron, deer and elk); the mod's by display name with its variants folded; unnamed
# master forms take their race's kind. Humanoids, named one-offs and forms whose race lives in a DLC master the
# scan does not read are out; domestic kinds are counted apart (docs/research/2026-11-03/creature-kinds-per-region.md).
RACE_KIND = {
    "WolfRace": "wolf", "BearBrownRace": "bear", "BearBlackRace": "bear", "BearSnowRace": "bear", "FoxRace": "fox",
    "MudcrabRace": "mudcrab", "HareRace": "hare", "TrollFrostRace": "frost troll", "TrollRace": "troll",
    "SabreCatRace": "sabre cat", "SabreCatSnowyRace": "sabre cat", "FrostbiteSpiderRace": "frostbite spider",
    "FrostbiteSpiderRaceLarge": "frostbite spider", "FrostbiteSpiderRaceGiant": "frostbite spider", "ElkRace": "deer",
    "DeerRace": "deer", "IceWraithRace": "ice wraith", "SkeeverRace": "skeever", "SkeeverWhiteTailRace": "skeever",
    "GoatRace": "goat", "DragonRace": "dragon", "HorkerRace": "horker", "ChaurusRace": "chaurus",
    "ChaurusReaperRace": "chaurus", "SlaughterfishRace": "slaughterfish", "GiantRace": "giant",
    "C00GiantOutsideWhiterunRace": "giant", "MammothRace": "mammoth", "WitchlightRace": "wisp", "WispRace": "wisp",
    "HagravenRace": "hagraven", "SprigganRace": "spriggan", "SprigganMatronRace": "spriggan",
    "AtronachFrostRace": "atronach", "AtronachFlameRace": "atronach", "AtronachStormRace": "atronach",
    "DwarvenCenturionRace": "dwarven centurion",
    "ChickenRace": "*chicken", "CowRace": "*cow", "DogRace": "*dog", "DogCompanionRace": "*dog", "HorseRace": "*horse",
    "CartHorseRace": "*horse"}
# the mod's display names folded to one kind (variants, sizes, misspellings)
NAME_KIND = {"bear cub": "bear", "forest spider queen": "forest spider", "dragling blind": "dragling",
             "adolescent serpant": "serpent", "guardian of the forest": "forest guardian", "megalanian": "megalania",
             "blue megalania": "megalania"}
# the mod's own named forms: out when the race is a person's (a draugr-race corpse leech is a creature kind)
PERSON = ("Nord", "Imperial", "Breton", "Redguard", "HighElf", "DarkElf", "WoodElf", "Orc", "Argonian", "Khajiit",
          "Elder", "Child", "DragonPriest", "Dremora", "Vampire")
EDID_KIND = {"EncWolfRed": "red wolf", "EncGoatDomestic": "*goat"}  # Skyrim forms the mod places as another kind
WEATHER_SKIP = ("NoPrecip",)
CITY = ("WeatherHighHrothgar", "WeatherCoastFog", "WeatherDarklightTower", "WeatherFFRiften", "WeatherFalkreath",
        "WeatherWinterhold", "WeatherLabyrinthian", "WeatherThroatOfTheWorld", "WeatherDA02")
MOD = Path.home() / ".argonia" / "stack" / "MO2" / "mods" / "bmv" / "Black Marsh.esm"
MOD_MAIN = "BlackMarsh"
BARS = Path(__file__).resolve().parents[3] / "data" / "creature-kind-bars.json"


def kind_of(s, k: int, race_scan=None, mod=False) -> str | None:
    """The species a creature NPC_ stands for, '*name' for a domestic kind, None when it is no creature kind."""
    n = s.npcs[k]
    if race_scan is None:  # a Skyrim.esm form
        if mod and n.edid in EDID_KIND:
            return EDID_KIND[n.edid]
        r = s.races.get(n.race)
        if r is None or any(h.lower() in r.edid.lower() for h in HUMANOID):
            return None
        return RACE_KIND.get(r.edid)
    r = s.races.get(n.race) or race_scan.races.get((n.race or 0) & 0xFFFFFF)  # the mod's own race, else Skyrim's
    if r is None or not n.name or any(h.lower() in r.edid.lower() for h in PERSON):
        return None  # a DLC race the scan does not read, an unnamed mod form, a person
    nm = n.name.lower()
    return NAME_KIND.get(nm, nm)


def skyrim_kinds(s=None, t=None) -> dict[str, dict]:
    """Skyrim.esm: per Weather* biome region (NoPrecip merged into its parent, city sub-regions out) the cells and
    the wild kinds reachable from its exterior creature refs (levelled lists expanded)."""
    s, t = s or scan(), t or load.tamriel()
    regn = {f: v[1] for f, v in t["forms"].items() if v[0] == "REGN"}
    cell_reg = {}
    for xy, c in t["cells"].items():
        for r in c["regions"]:
            e = regn.get(r, "")
            if e.startswith("Weather"):
                e = e.replace("NoPrecip", "")
                if e not in CITY:
                    cell_reg.setdefault(xy, set()).add(e)  # a cell may carry two biome regions: it counts in each
    out = {}
    for es in cell_reg.values():
        for e in es:
            out.setdefault(e, {"cells": 0, "kinds": set()})["cells"] += 1
    for a in s.achrs:
        if a.world != load.TAMRIEL or a.cell not in cell_reg:
            continue
        for k in actors.resolve(s, a.base):
            if k in s.npcs:
                kd = kind_of(s, k)
                if kd:
                    for e in cell_reg[a.cell]:
                        out[e]["kinds"].add(kd)
    return out


def mod_kinds(m=None, s=None) -> dict[str, dict]:
    """Black Marsh.esm: per worldspace (its cells carry no REGN) the LAND cells, the wild kinds, and the most kinds
    any square window of n x n cells holds (for the equal-area bar of a smaller region)."""
    m, s = m or actors.scan(MOD), s or scan()
    own = len(m.masters)
    per = {}
    for a in m.achrs:
        w = m.worlds.get(a.world)
        if w is None or w == "Tamriel" or a.cell is None:
            continue
        i = a.base >> 24
        if i >= own:
            S, f, rs = m, a.base, s
        elif m.masters[i] == "Skyrim.esm":
            S, f, rs = s, a.base & 0xFFFFFF, None
        else:
            continue
        for k in actors.resolve(S, f):
            if k in S.npcs:
                kd = kind_of(S, k, rs) if S is m else kind_of(s, k, mod=True)
                if kd:
                    per.setdefault(w, {}).setdefault(a.cell, set()).add(kd)
    land = mod_land_cells()
    out = {}
    for w, cells in per.items():
        wild = set().union(*cells.values())
        win = {}
        for n in (3, 5, 9, 13, 17, 21, 25, 29, 33):
            best = 0
            xs, ys = [c[0] for c in cells], [c[1] for c in cells]
            for x0 in range(min(xs) - n + 1, max(xs) + 1):
                for y0 in range(min(ys) - n + 1, max(ys) + 1):
                    k = {kd for (x, y), v in cells.items() if x0 <= x < x0 + n and y0 <= y < y0 + n for kd in v
                         if not kd.startswith("*")}
                    best = max(best, len(k))
            win[n * n] = best
        out[w] = {"cells": land.get(w, 0), "kinds": wild, "window_max": win}
    return out


def mod_land_cells() -> dict[str, int]:
    """LAND records per worldspace of the mod (its exterior extent)."""
    import struct
    import zlib
    blob, out, cur = MOD.read_bytes(), {}, {}

    def walk(i, end, wname):
        while i < end:
            sig, size = blob[i:i + 4], struct.unpack_from("<I", blob, i + 4)[0]
            if sig == b"GRUP":
                label, gt = struct.unpack_from("<Ii", blob, i + 8)
                if gt == 0 and blob[i + 8:i + 12] not in (b"WRLD", b"CELL"):
                    i += size
                    continue
                walk(i + 24, i + size, cur.get(label, wname) if gt == 1 else wname)
                i += size
                continue
            if sig == b"WRLD":
                flags, fid = struct.unpack_from("<II", blob, i + 8)
                b = blob[i + 24:i + 24 + size]
                b = zlib.decompress(b[4:]) if flags & 0x40000 else b
                cur[fid] = dict(actors._subs(b)).get(b"EDID", b"").split(b"\0")[0].decode("latin1")
            elif sig == b"LAND" and wname:
                out[wname] = out.get(wname, 0) + 1
            i += 24 + size

    walk(struct.unpack_from("<I", blob, 4)[0] + 24, len(blob), None)
    return out


def kind_bars() -> dict:
    """The numbers the creatures check holds our region classes to (cached in data/, counts only, 0003)."""
    s = scan()
    sk = skyrim_kinds(s)
    md = mod_kinds(s=s)
    wild = lambda v: sorted(k for k in v["kinds"] if not k.startswith("*"))
    return {"source": "python3 -m tools.argonia_world.vanilla.creatures --bars (Skyrim.esm + Update.esm; Black Marsh.esm)",
            "skyrim": {e: {"cells": v["cells"], "wild_kinds": len(wild(v))} for e, v in sorted(sk.items())},
            "mod": {w: {"cells": v["cells"], "wild_kinds": len(wild(v)), "window_max": v["window_max"]}
                    for w, v in sorted(md.items())},
            "mod_main": MOD_MAIN}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json")
    ap.add_argument("--bars", action="store_true", help="the kinds-per-region bars, written to data/")
    a = ap.parse_args(argv)
    if a.bars:
        b = kind_bars()
        BARS.write_text(json.dumps(b, indent=1) + "\n")
        print(json.dumps(b, indent=1))
        return 0
    m = measure()
    txt = json.dumps(m, indent=1, default=str)
    if a.json:
        Path(a.json).parent.mkdir(parents=True, exist_ok=True)
        Path(a.json).write_text(txt + "\n")
    print(txt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
