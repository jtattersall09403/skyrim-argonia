"""Every creature the pinned Black Marsh mods ship, and how each mod places its own (1.15 §g.2).

    python3 -m tools.argonia_world.creatures inventory [--json out/creatures/inventory.json]

Read from the laid stack (~/.argonia/stack/MO2/mods, never the repo: decision 0003). A creature is an NPC_ whose
race is not a person's (actors.HUMANOID words). For each placed ACHR in the mod's own exterior worldspaces: in
water (z under the cell's water, XCLW or the world's default) or on land, grouped (another creature ACHR within
GROUP_M) or alone. MAP joins each mod form to our creature row by editor-ID or race words.
"""
from __future__ import annotations

import math
from collections import Counter, defaultdict
from pathlib import Path

from tools.argonia_world.creatures import actors
from tools.argonia_world.skyrim_units import UNITS_PER_METRE

MODS = Path.home() / ".argonia" / "stack" / "MO2" / "mods"
PLUGINS = (
    ("bmv", "Black Marsh.esm"),
    ("king-of-the-murkmire", "King of the Murkmire.esp"),
    ("htbm", "Here There Be Monsters.esp"),
    ("htbm-cipactli", "Here There Be Monsters - Curse of Cipactli.esp"),
    ("depths-of-skyrim", "DepthsOfSkyrim.esp"),
    ("mud-mother-grove", "ArgonianLakeHouse.esl"),
    ("tropical-skyrim-sse", "Tropical Skyrim.esp"),
    ("tropical-skyrim-sse", "Tropical Skyrim -- Birds.esp"),
)
HUMANOID = ("nord", "imperial", "breton", "redguard", "highelf", "darkelf", "woodelf", "orc", "argonian", "khajiit",
            "elder", "child", "vampire", "afflicted", "dremora", "manakin", "default", "naga", "lilmothiit", "kothringi",
            "saxhleel", "human", "elf", "tsaesci")
GROUP_M = 15.0


def creature_npcs(s: actors.Scan, base_races: dict[int, actors.Race]) -> dict[int, tuple[actors.Npc, str]]:
    out = {}
    for f, n in s.npcs.items():
        r = s.races.get(n.race) or base_races.get(n.race & 0xFFFFFF if n.race is not None else -1)
        re = r.edid if r else "?"
        if r is not None and not any(h in re.lower() for h in HUMANOID):
            out[f] = (n, re)
    return out


def water_level(s: actors.Scan, a: actors.Achr) -> float:
    """The water over an ACHR's cell (units): XCLW, else the world's default; a no-water sentinel (> 1e6) is none."""
    w = s.cell_water.get((a.world, *a.cell)) if a.cell else None
    if w is None or abs(w) > 1e6:
        w = s.world_water.get(a.world)
    return -1e9 if w is None or abs(w) > 1e6 else w


def run(skyrim_races: dict[int, actors.Race] | None = None) -> dict:
    res = {}
    for mod, name in PLUGINS:
        p = MODS / mod / name
        if not p.exists():
            res[name] = {"missing": str(p)}
            continue
        s = actors.scan(p)
        own = len(s.masters)
        cr = creature_npcs(s, skyrim_races or {})
        new = {f: v for f, v in cr.items() if f >> 24 == own}
        placed = defaultdict(list)
        for a in s.achrs:
            if a.base in cr:
                placed[a.base].append(a)
        ext = [a for v in placed.values() for a in v if a.world is not None]
        wet = grouped = 0
        for a in ext:
            wl = water_level(s, a)
            wet += a.pos[2] < wl
            grouped += any(b is not a and math.dist(a.pos[:2], b.pos[:2]) < GROUP_M * UNITS_PER_METRE for b in ext
                           if b.cell == a.cell)
        res[name] = {
            "masters": s.masters,
            "creature_npcs": len(cr), "new_creature_npcs": len(new),
            "new_races": sorted({r.edid for f, r in s.races.items() if f >> 24 == own}),
            "forms": [{"form": f"{f & 0xFFFFFF:06X}:{name}" if f >> 24 == own else f"{f:08X}", "edid": n.edid,
                       "name": n.name, "race": re, "aggression": n.aggression, "confidence": n.confidence,
                       "level": n.level, "placed": len(placed.get(f, []))} for f, (n, re) in sorted(cr.items())],
            "achr_exterior": len(ext), "achr_interior": sum(1 for v in placed.values() for a in v if a.world is None),
            "exterior_in_water": wet, "exterior_grouped": grouped,
            "worlds": dict(Counter(s.worlds.get(a.world, hex(a.world)) for a in ext)),
            "lvln": len(s.lvlns), "eczn": len(s.ecznS),
        }
    return res
