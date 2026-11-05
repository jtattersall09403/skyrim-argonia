"""The water's records: the WATR types (intermediate records, README contract; no water-plane activators since
1.15: every cell's water is its own XCLW/XCWT, decision 0033 §1), and the per-cell stream `out/water/cells.jsonl`
that the worldspace writer applies to each exterior CELL through `WaterRecords.ApplyCell` (agreed with the 2.W1
lane on 2026-10-29).

Plugin (decision 0031): the water belongs to `ArgoniaWorld.esm` with the cells it stands in (the WRLD's default
and LOD water link the sea type, and that plugin is the master). FormIDs come from a reserved range computed from
the cell grid, as 0031 §3 rules for the generated master: the types at WATER_BASE + 0..len(TYPES)-1, each province
cell a slot of REFS_PER_CELL ids from WATER_BASE + 0x100. A cell needing more refs than its slot is a plan error.

Types the Skyrim way (round 5, docs/research/2026-11-03/water-types.md, owner #37): Skyrim varies water by WATR
parameters only and gives each cell one type (XCWT); its sea and lakes are the worldspace default DefaultWater, its
marshes DefaultMarshWater with a DefaultMarshWaterTransition rim, its rivers RiverWaterFlowNE/NW/SE and its creeks
CreekWaterFlowSE/SW, a flow direction baked per record. Each of our types copies one vanilla or dependency editor id
whole (its shading body: textures, colours, fog, winds, specular; a bare WATR draws flat opaque white, round 1),
and the copy is of the record the game RESOLVES: the last plugin in the load order that carries it (`winners`).
Round 4 copied Skyrim.esm's DefaultWater, which Update.esm and Tropical Skyrim.esp override, so the game never
showed the record we copied. Only the name is ours, and on the two directions vanilla never made (rivers flowing
SW, creeks flowing NE/NW) the flow (NAM0 linear velocity and the three noise winds' directions) of the opposite
record turned half a circle: the named `set` fields, nothing else.

The per-cell type keys on what the database already holds (cell_water's water class, the body's kind and altitude
band, the reach's river strahler and its centreline heading); `cell_type` is the rule.
"""
from __future__ import annotations

import os
import struct
from functools import lru_cache
from pathlib import Path

from tools.argonia_world import skyrim_units as su

PLUGIN = "ArgoniaWorld.esm"
WATER_BASE = 0x100000  # past the terrain's CELL/LAND range (0x810 + 2 x 262^2 = 0x22A30)
REFS_PER_CELL = 256
PROVINCE_CELLS = su.PROVINCE_CELLS
GAME_DATA = Path(os.environ.get("ARGONIA_GAME_ROOT", Path.home() / "games/skyrimse")) / "Data"

QUADS = ("ne", "nw", "se", "sw")
# type -> (name, the editor id it copies, flowing, the opposite direction's type it turns half a circle or None).
# The first is the sea (WRLD NAM2/NAM3). Winners measured 2026-11-03 over the stack's load order: DefaultWater,
# DefaultMarshWater and DefaultMarshWaterTransition = Tropical Skyrim.esp; DefaultBlackmarshWater = King of the
# Murkmire.esp (not used since r5 black-water: olive 130,116,34, not black); the black type copies Dawnguard's
# DLC01DarkFallCaveDarkStillWater whole (lane 1.15-r6-water-look-2: Bethesda's darkest still water, deep 12,12,12,
# reflection colour 10,10,5, reflectivity 0.28, fresnel 0; MurkyWater's olive reflection colour 32,35,27 under a lit
# canopy read the swamp dark olive in r6-chain23); DefaultWaterCold = Dawnguard.esm;
# RiverWaterFlowNE/NW/SE and CreekWaterFlowSE/SW = Update.esm.
TYPES: dict[str, tuple[str, str, bool, str | None]] = {
    "sea": ("Sea", "DefaultWater", False, None),
    "lake": ("Lake Water", "DefaultWater", False, None),  # Skyrim's lakes are its sea's type; ours its twin
    "marsh": ("Marsh Water", "DefaultMarshWater", False, None),  # marsh-deep, backswamp
    "black": ("Black Water", "DLC01DarkFallCaveDarkStillWater", False, None),  # swamp, marsh-fringe (r6 water-look-2)
    "cold": ("Cold Water", "DefaultWaterCold", False, None),  # tarns, montane and upland ponds and pools
    "brackish": ("Brackish Water", "DefaultMarshWaterTransition", False, None),  # the tidal rim
    "river-ne": ("River", "RiverWaterFlowNE", True, None),
    "river-nw": ("River", "RiverWaterFlowNW", True, None),
    "river-se": ("River", "RiverWaterFlowSE", True, None),
    "river-sw": ("River", "RiverWaterFlowNE", True, "ne"),
    "creek-se": ("Stream", "CreekWaterFlowSE", True, None),
    "creek-sw": ("Stream", "CreekWaterFlowSW", True, None),
    "creek-nw": ("Stream", "CreekWaterFlowSE", True, "se"),
    "creek-ne": ("Stream", "CreekWaterFlowSW", True, "sw"),
}
EMIT_TYPES = tuple(TYPES)
STILL_KINDS = {"marsh-deep": "marsh", "backswamp": "marsh", "swamp": "black", "marsh-fringe": "black",
               "tarn-upland": "cold", "plunge-pool": "cold", "lake-lowland": "lake", "lagoon": "sea",
               "mudflat": "brackish"}


def type_edid(t: str) -> str:
    return f"ARG_WATR_{t.replace('-', '_')}"


def type_key(t: str) -> str:
    return f"{WATER_BASE + EMIT_TYPES.index(t):06X}:{PLUGIN}"


def is_flow(t: str) -> bool:
    return TYPES[t][2]


def quadrant(dx_east: float, dy_north: float) -> str:
    """A heading quantised to the four baked directions (NAM0's x east, y north, as RiverWaterFlowNE's (2.54, 1.35))."""
    return ("n" if dy_north >= 0 else "s") + ("e" if dx_east >= 0 else "w")


def cell_type(wt: str, kind: str | None, band: str | None, reach_id: str | None, strahler: int | None,
              quad: str | None) -> str:
    """The emitted type of a cell. A river's own cell (a reach's level, no body's) flows, its record by strahler
    (1 a creek, 2+ a river; a reach of no river, the tidal channels, a river) and its reach's heading; every other
    is still, by its water class and body kind."""
    if wt == "sea":
        return "sea"
    if wt == "brackish":
        return "brackish"
    if reach_id and not kind:
        return f"{'creek' if strahler == 1 else 'river'}-{quad or 'ne'}"
    if kind is None:
        return "black" if wt == "blackwater" else "lake"  # a step's foot or a bank fill: the class's still water
    if kind in STILL_KINDS:
        return STILL_KINDS[kind]
    if kind in ("pond", "pool"):
        return "lake" if band in ("lowland", "tidal") else "cold"
    raise ValueError(f"water: body kind {kind!r} has no type")


def ref_key(cx: int, cy: int, k: int) -> str:
    x0, y0 = su.PROVINCE_CELL_SW
    i = (cy - y0) * PROVINCE_CELLS + (cx - x0)
    if not (0 <= i < PROVINCE_CELLS ** 2) or not (0 <= k < REFS_PER_CELL):
        raise ValueError(f"cell ({cx},{cy}) ref {k}: outside the reserved water range")
    return f"{WATER_BASE + 0x100 + i * REFS_PER_CELL + k:06X}:{PLUGIN}"


def top_group(path: Path, sig: bytes) -> list:
    """A plugin's records of one top group (esm.Record), seeking past the other groups (Skyrim.esm is 250 MB)."""
    from tools.argonia_world.terrain import esm
    with open(path, "rb") as f:
        head = f.read(24)
        f.seek(struct.unpack_from("<I", head, 4)[0] + 24)
        while len(g := f.read(24)) == 24:
            size = struct.unpack_from("<I", g, 4)[0]
            if g[8:12] == sig:
                body = g + f.read(size - 24)
                return [r for r in esm.records(b"TES4" + struct.pack("<I", 0) + bytes(16) + body) if r.sig == sig.decode()]
            f.seek(size - 24, 1)
    return []


@lru_cache(maxsize=4)
def winners(data: Path = GAME_DATA) -> dict[str, tuple[str, object]]:
    """Every WATR editor id -> (the last plugin in the load order carrying it, its record): what the game draws."""
    from tools.argonia_world.intermediate import load_order
    out: dict[str, tuple[str, object]] = {}
    for p in load_order(Path(data)):
        for r in top_group(Path(data) / p, b"WATR"):
            out[r.first("EDID").rstrip(b"\0").decode()] = (p, r)
    return out


def template_of(t: str, data: Path = GAME_DATA) -> str:
    edid = TYPES[t][1]
    return f"{winners(Path(data))[edid][0]}:{edid}"


def flow_set(t: str, data: Path = GAME_DATA) -> dict:
    """The fields a type changes from its template: a turned type its NAM0 and the three noise winds' directions, half
    a circle; a still type but the sea its NAM0 to nought (lane 1.15-r6-water-steps, owner play test 3 finding 20: the
    lake, cold and marsh winners drift at 0.15-0.37; Skyrim's own still record, MurkyWater, carries NAM0 0, 0, 0)."""
    r = winners(Path(data))[TYPES[t][1]][1]
    if not TYPES[t][2]:
        v = struct.unpack("<3f", r.first("NAM0"))
        return {"linearVelocity": [0.0, 0.0, 0.0]} if t != "sea" and any(v) else {}
    if TYPES[t][3] is None:
        return {}
    v = struct.unpack("<3f", r.first("NAM0"))
    d = struct.unpack_from("<3f", r.first("DNAM"), 25 * 4)
    return {"linearVelocity": [-v[0], -v[1], v[2]], "windDirections": [(a + 180.0) % 360.0 for a in d]}


# types that meet at one level along a cell line share the shallow colour, as Skyrim.esm's DefaultWater,
# DefaultMarshWater and DefaultMarshWaterTransition all carry 37,52,37 (lane 1.15-r6-shores-slope: 119 of Tamriel's
# 21,162 same-level neighbour pairs differ in type, 34 of them Transition beside DefaultWater or the marsh). Tropical
# Skyrim gives DefaultWater a cyan shallow 81,174,165 and the Transition an olive 49,56,37, so our tidal rim drew a
# hard cyan strip at zero depth along the sea cell beside it (round-6 brackish-rim s0, y 620-660; 286 of our 287
# same-level type seams are sea beside brackish). The brackish rim takes the sea's shallow colour; its deep stays its own
SHALLOW_FROM = {"brackish": "sea"}


def shallow_of(t: str, data: Path = GAME_DATA) -> list[int]:
    d = winners(Path(data))[TYPES[t][1]][1].first("DNAM")
    return list(d[40:43])


def records(data: Path = GAME_DATA) -> list[dict]:
    """The WATR intermediate records (README contract; units, winners and choices resolved here)."""
    out = []
    for t in EMIT_TYPES:
        rec = {"type": "WATR", "formKey": type_key(t), "edid": type_edid(t), "template": template_of(t, data),
               "layer": "base:water", "name": TYPES[t][0], "flow": is_flow(t)}
        s = flow_set(t, data)
        if t in SHALLOW_FROM and shallow_of(SHALLOW_FROM[t], data) != shallow_of(t, data):
            s = {**s, "shallowColor": shallow_of(SHALLOW_FROM[t], data)}
        if s:
            rec["set"] = s
        out.append(rec)
    return out
