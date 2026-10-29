"""The water's records: four WATR types and four water-plane activators (intermediate records, README contract),
and the per-cell stream `out/water/cells.jsonl` that the worldspace writer applies to each exterior CELL through
`WaterRecords.ApplyCell` (agreed with the 2.W1 lane on 2026-10-29).

Plugin (decision 0031): the water belongs to `ArgoniaWorld.esm` with the cells it stands in (the WRLD's default
water links the sea type, and that plugin is the master). FormIDs come from a reserved range computed from the cell
grid, as 0031 §3 rules for the generated master: the types and activators at WATER_BASE + 0..7, each province cell
a slot of REFS_PER_CELL ids from WATER_BASE + 0x100. A cell needing more refs than its slot is a plan error.

WATR values are ours, chosen as a starting point for the Community Shaders tuning (2.W2 §a: tuned in game until a
reader judges them good against reference stills); nothing is copied from a vanilla record.
"""
from __future__ import annotations

from tools.argonia_world import skyrim_units as su
from tools.argonia_world.water.classify import WATER_TYPES

PLUGIN = "ArgoniaWorld.esm"
WATER_BASE = 0x100000  # past the terrain's CELL/LAND range (0x810 + 2 x 262^2 = 0x22A30)
REFS_PER_CELL = 256
PLANE_MODEL = "Water\\Water1024.nif"
PROVINCE_CELLS = su.PROVINCE_CELLS

# name, opacity, shallow, deep, reflection colour, fog above near/far, fog under near/far, fog amounts
TYPES = {
    "sea": ("Sea", 40, [74, 112, 104], [12, 38, 44], [160, 186, 190], (0.0, 150.0), (0.0, 1200.0), (0.4, 0.85)),
    "brackish": ("Brackish Water", 60, [92, 104, 72], [30, 40, 26], [150, 160, 140], (0.0, 110.0), (0.0, 600.0),
                 (0.5, 0.9)),
    "fresh": ("Fresh Water", 35, [86, 118, 98], [22, 48, 42], [170, 190, 186], (0.0, 140.0), (0.0, 900.0), (0.35, 0.8)),
    "black": ("Black Water", 90, [52, 44, 26], [14, 12, 6], [120, 116, 96], (0.0, 60.0), (0.0, 220.0), (0.7, 1.0)),
}


def type_edid(t: str) -> str:
    return f"ARG_WATR_{t}"


def plane_edid(t: str) -> str:
    return f"ARG_WaterPlane_{t}"


def type_key(t: str) -> str:
    return f"{WATER_BASE + WATER_TYPES.index(t):06X}:{PLUGIN}"


def plane_key(t: str) -> str:
    return f"{WATER_BASE + len(WATER_TYPES) + WATER_TYPES.index(t):06X}:{PLUGIN}"


def ref_key(cx: int, cy: int, k: int) -> str:
    x0, y0 = su.PROVINCE_CELL_SW
    i = (cy - y0) * PROVINCE_CELLS + (cx - x0)
    if not (0 <= i < PROVINCE_CELLS ** 2) or not (0 <= k < REFS_PER_CELL):
        raise ValueError(f"cell ({cx},{cy}) ref {k}: outside the reserved water range")
    return f"{WATER_BASE + 0x100 + i * REFS_PER_CELL + k:06X}:{PLUGIN}"


def records() -> list[dict]:
    """The WATR and ACTI intermediate records (README contract; units and choices resolved here)."""
    out = []
    for t in WATER_TYPES:
        name, op, shallow, deep, refl, fog_above, fog_under, amounts = TYPES[t]
        out.append({"type": "WATR", "formKey": type_key(t), "edid": type_edid(t), "layer": "base:water",
                    "name": name, "opacity": op, "shallowColor": shallow, "deepColor": deep,
                    "reflectionColor": refl, "fogAbove": [fog_above[0], fog_above[1], amounts[0]],
                    "fogUnder": [fog_under[0], fog_under[1], amounts[1]]})
    for t in WATER_TYPES:
        out.append({"type": "ACTI", "formKey": plane_key(t), "edid": plane_edid(t), "layer": "base:water",
                    "model": PLANE_MODEL, "bounds": [[-512, -512, 0], [512, 512, 0]], "waterType": type_key(t)})
    return out
