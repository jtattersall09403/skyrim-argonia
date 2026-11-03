"""The water's records: four WATR types (intermediate records, README contract; no water-plane activators since
1.15: every cell's water is its own XCLW/XCWT, decision 0033 §1),
and the per-cell stream `out/water/cells.jsonl` that the worldspace writer applies to each exterior CELL through
`WaterRecords.ApplyCell` (agreed with the 2.W1 lane on 2026-10-29).

Plugin (decision 0031): the water belongs to `ArgoniaWorld.esm` with the cells it stands in (the WRLD's default
water links the sea type, and that plugin is the master). FormIDs come from a reserved range computed from the cell
grid, as 0031 §3 rules for the generated master: the types and activators at WATER_BASE + 0..7, each province cell
a slot of REFS_PER_CELL ids from WATER_BASE + 0x100. A cell needing more refs than its slot is a plan error.

Each type's shading body (noise textures, specular, fresnel, displacement) is Skyrim.esm's DefaultWater (TEMPLATE,
decision 0034: every vanilla WATR carries them, and a bare one draws flat opaque white, round 1 stills 2026-11-02);
only the name is ours; opacity, colours and fog are the template's too (round 4).
"""
from __future__ import annotations

from tools.argonia_world import skyrim_units as su
from tools.argonia_world.water.solve import WATER_TYPES

PLUGIN = "ArgoniaWorld.esm"
WATER_BASE = 0x100000  # past the terrain's CELL/LAND range (0x810 + 2 x 262^2 = 0x22A30)
REFS_PER_CELL = 256
PROVINCE_CELLS = su.PROVINCE_CELLS
# The shading body each type copies (WaterRecords.cs), still or flowing as Skyrim.esm does it (measured
# 2026-11-03, the XCWT of Tamriel's 11,186 cells): its lakes and ponds are the world's default DefaultWater (10,742
# cells carry no XCWT) and its marshes DefaultMarshWater; its rivers RiverWaterFlowNE/NW/SE, CreekWaterFlow* and
# DefaultRiverWater (298 cells). The two differ in the noise layers' winds (DNAM): DefaultWater's speeds
# 0.019/0.013/0.096, DefaultRiverWater's 0.044/0.033/0.145 with its flow normals on. Round 3 copied DefaultWater
# into every type, rivers included, so nothing told still water from flowing (owner play test 3, finding 19).
STILL_TEMPLATE = "Skyrim.esm:DefaultWater"
FLOW_TEMPLATE = "Skyrim.esm:DefaultRiverWater"
TEMPLATE = STILL_TEMPLATE
NOISE_WIND_SPEED = {STILL_TEMPLATE: (0.019, 0.013, 0.096), FLOW_TEMPLATE: (0.044, 0.033, 0.145)}  # DNAM, measured
FLOW = "-flow"  # a river cell's type: its class's flowing twin (the sea has none)
EMIT_TYPES = WATER_TYPES + tuple(t + FLOW for t in WATER_TYPES if t != "sea")  # keys WATER_BASE + 0..6

# The name is the only field ours (round 4, decision 0034): opacity, the three colours, the fog above and below and every
# other DNAM field are the template's own. The round-3/4 overrides (opacity 35-90 against vanilla's 30 and 50, fog
# near 0 against -10 and -500, brighter colours) were a guess, and the shore stills read marbled, blotchy, black and
# green with them; the authored look comes later by a decision (2.W2 a).
TYPES = {"sea": "Sea", "brackish": "Brackish Water", "fresh": "Fresh Water", "blackwater": "Black Water"}


def type_edid(t: str) -> str:
    return f"ARG_WATR_{t}"


def type_key(t: str) -> str:
    return f"{WATER_BASE + EMIT_TYPES.index(t):06X}:{PLUGIN}"


def template_of(t: str) -> str:
    return FLOW_TEMPLATE if t.endswith(FLOW) else STILL_TEMPLATE


def cell_type(wt: str, body_id: str | None, reach_id: str | None) -> str:
    """The emitted type of a cell: a river's own cell (a reach's level, no body's) flows; every other is still."""
    return wt + FLOW if reach_id and not body_id and wt != "sea" else wt


def ref_key(cx: int, cy: int, k: int) -> str:
    x0, y0 = su.PROVINCE_CELL_SW
    i = (cy - y0) * PROVINCE_CELLS + (cx - x0)
    if not (0 <= i < PROVINCE_CELLS ** 2) or not (0 <= k < REFS_PER_CELL):
        raise ValueError(f"cell ({cx},{cy}) ref {k}: outside the reserved water range")
    return f"{WATER_BASE + 0x100 + i * REFS_PER_CELL + k:06X}:{PLUGIN}"


def records() -> list[dict]:
    """The WATR intermediate records (README contract; units and choices resolved here)."""
    out = []
    for t in EMIT_TYPES:
        out.append({"type": "WATR", "formKey": type_key(t), "edid": type_edid(t.replace("-", "_")),
                    "template": template_of(t), "layer": "base:water", "name": TYPES[t.removesuffix(FLOW)]})
    return out
