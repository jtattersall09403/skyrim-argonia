"""Skyrim's unit facts, the only place they live (decision 0009 §4; CLAUDE.md "Skyrim unit facts live only in
the units module"). Every other module converts through these names; a literal 70.03, 4096 or 0x800 elsewhere
is a bug the gate's grep finds (tests/test_skyrim_units.py).

World frame: metres, x east, z up, yaw degrees clockwise from north (the imported records' frame). The imported
province records' y runs SOUTH from the province's north-west corner (old 0003 "X east, Z south"; measured by 2.W1
on 2026-10-29: route-grade profiles sit on the heightfield at row = y / sample, row 0 is the north edge), so an
exterior position goes through `province_to_skyrim`, never `metres_to_units` on y alone.
Skyrim frame: units, same axes, rotations in radians applied Z then Y then X (Euler ZYX, extrinsic).
"""
from __future__ import annotations

import math

# --- distance -------------------------------------------------------------------------------------------------
UNITS_PER_METRE = 70.03  # 0009 §4; the heightfield's 1.828 m sample is 128 units
VERTEX_SPACING_UNITS = 128  # LAND vertex spacing
CELL_UNITS = 4096  # an exterior cell's side
LAND_VERTS = 33  # LAND vertices per cell side (32 quads + the shared edge)
LAND_QUADRANT_LAYERS = 6  # texture layers per quadrant, the base layer excluded
VHGT_STEP_UNITS = 8  # one VHGT signed byte step
CELL_METRES = CELL_UNITS / UNITS_PER_METRE  # 58.49 m


def metres_to_units(m: float) -> float:
    return m * UNITS_PER_METRE


def units_to_metres(u: float) -> float:
    return u / UNITS_PER_METRE


def cell_of(x_units: float, y_units: float) -> tuple[int, int]:
    """The exterior cell grid coordinate holding a Skyrim-frame point."""
    return math.floor(x_units / CELL_UNITS), math.floor(y_units / CELL_UNITS)


def cell_origin(cx: int, cy: int) -> tuple[int, int]:
    """South-west corner of a cell, in units."""
    return cx * CELL_UNITS, cy * CELL_UNITS


# --- rotation -------------------------------------------------------------------------------------------------
def yaw_to_rot(yaw_deg: float) -> tuple[float, float, float]:
    """A world-frame yaw (degrees clockwise from north) as Skyrim's (rx, ry, rz) radians.

    Skyrim's z rotation is clockwise seen from above with 0 facing north (+y), the same sense as the world frame,
    so only the unit changes; it is normalised into [0, 2π) as the CK writes it.
    """
    return 0.0, 0.0, math.radians(yaw_deg) % (2 * math.pi)


def rounded(v: float, places: int = 4) -> float:
    """Positions and angles are written at a fixed precision so regeneration is byte-stable."""
    r = round(v, places)
    return 0.0 if r == 0 else r  # no -0.0


# --- calendar ---------------------------------------------------------------------------------------------------
MONTH_DAYS = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)  # Skyrim's calendar (GameMonth 0..11), no leap years


# --- FormIDs and plugins --------------------------------------------------------------------------------------
FORMID_FIRST = 0x800  # the first object id a plugin may allocate (lower ids are the engine's)
FORMID_LAST = 0xFFFFFF  # the last for a full (non-light) master
LIGHT_LAST = 0xFFF  # the last for an ESL-flagged plugin
EDITOR_ID_MAX = 99  # the CK's limit; voice paths take only the first 25 (gotcha in prior-art §3)

# The runtime's own masters, in load order (decision 0012's context); Creation Club masters follow from
# Skyrim.ccc for those present, then the dependency plugins (data/dependencies.json), then ours.
OFFICIAL_MASTERS = ("Skyrim.esm", "Update.esm", "Dawnguard.esm", "HearthFires.esm", "Dragonborn.esm")
ENGINE_MARKER_HEADING = "000034:Skyrim.esm"  # XMarkerHeading: the engine's own heading marker
SILENT_MUSIC_TRACK = "0137FA:Skyrim.esm"  # _MUSExploreSILENT30, a silent MUST: vanilla _NONE's one track. A MUSC with no
#   track is an access violation when the engine picks one (SkyrimSE.exe+0327DC4, game-6), so every MUSC has this one
MAP_MARKER = "000010:Skyrim.esm"  # MapMarker: the static a map marker reference stands on

# --- items (1.3 §c) ---------------------------------------------------------------------------------------------
WEIGHT_PER_KG = 1.0  # a record's Weight is the world row's kilograms as they stand (Skyrim's Weight is unitless, ~kg)
BIPED_FIRST_SLOT = 30  # biped slot numbers run 30..61; the record stores them as bit (slot - 30) of a mask
DEFAULT_RACE = "000019:Skyrim.esm"  # DefaultRace: the race an ARMA names so every race can wear it
ARMOR_TYPE = {"light": "LightArmor", "heavy": "HeavyArmor"}  # a set's armour_class as the engine's ARMO type; no medium

WEAP_NEUTRAL_SPEED = WEAP_NEUTRAL_REACH = 1.0  # the engine's neutral multipliers; ArgoniaCore holds the measured values


def kg_to_weight(kg: float) -> float:
    return rounded(kg * WEIGHT_PER_KG, 4)


def biped_mask(slot: int) -> int:
    """The BOD2 biped-flag mask for one slot number (CK numbering, 30..61)."""
    if not BIPED_FIRST_SLOT <= slot < BIPED_FIRST_SLOT + 32:
        raise ValueError(f"biped slot {slot}: must be 30..61")
    return 1 << (slot - BIPED_FIRST_SLOT)


# --- skills -----------------------------------------------------------------------------------------------
# Our 27 skills (the world's `skill` table) onto Skyrim's 18 skill actor values (Mutagen's Skill names), for the
# engine-side records that need one (CLAS weights, NPC levelling). None: no Skyrim skill carries it; ArgoniaCore
# holds the real value (1.3).
SKILL_AV = {
    "longBlade": "OneHanded", "shortBlade": "OneHanded", "axe": "OneHanded", "blunt": "OneHanded",
    "spear": "TwoHanded", "marksman": "Archery", "block": "Block", "smithing": "Smithing",
    "heavyArmor": "HeavyArmor", "lightArmor": "LightArmor", "mediumArmor": None, "unarmored": None,
    "handToHand": None, "athletics": None, "acrobatics": None, "security": "Lockpicking", "sneak": "Sneak",
    "mercantile": "Speech", "speechcraft": "Speech", "alchemy": "Alchemy", "enchant": "Enchanting",
    "alteration": "Alteration", "conjuration": "Conjuration", "destruction": "Destruction",
    "illusion": "Illusion", "restoration": "Restoration", "mysticism": None,
}
SKYRIM_SKILLS = ("OneHanded", "TwoHanded", "Archery", "Block", "Smithing", "HeavyArmor", "LightArmor",
                 "Pickpocket", "Lockpicking", "Sneak", "Alchemy", "Speech", "Alteration", "Conjuration",
                 "Destruction", "Illusion", "Restoration", "Enchanting")
CLAS_WEIGHT_MAJOR, CLAS_WEIGHT_MINOR = 3, 1  # CLAS skill weights: relative, levelled NPCs only
CLAS_MAX_TRAINING = 50  # the CK's default training cap

# --- the province grid and LAND (2.W1; measured against Skyrim.esm's Tamriel LAND on 2026-10-29) -------------
# The frozen heightfield is 4033 x 4033 samples, row 0 the NORTH edge, column 0 the west edge, one sample per
# LAND vertex. Its sample is 1.82784 m (the hydrology solution's `mpp`), 128 units on the grid: positions on the
# province map to units through the grid (x_m / PROVINCE_SAMPLE_M * VERTEX_SPACING_UNITS), 70.028 units/m, so a
# placed thing and the ground under it share one conversion; heights use UNITS_PER_METRE (the 0.003 % gap is
# 0.2 m across the whole province, under any check).
PROVINCE_SAMPLE_M = 1.82784
PROVINCE_SAMPLES = 4033
QUADS_PER_CELL = LAND_VERTS - 1  # 32
PROVINCE_CELLS = (PROVINCE_SAMPLES - 1) // QUADS_PER_CELL  # 126
PROVINCE_CELL_SW = (-62, -62)  # the province's south-west cell (the old ESP export's -62..63 range, centred)
APRON_CELLS = 68  # the near apron ring beyond each border, in cells (the old apron-source-near pad of 2176 samples)
# VHGT: a float offset then 33 x 33 signed bytes; every value is in VHGT_STEP_UNITS steps (the offset too:
# 0 seams across 42 vanilla cell pairs with offset * 8, 973 units with offset * 1). Mutagen's HeightMap is
# indexed [x, y]: x the column west->east, y the row south->north; [0, y] is relative to [0, y-1], [x, y] to
# [x-1, y]. VNML is 33 x 33 signed-byte unit normals scaled by VNML_SCALE ([20, 14, 124] on vanilla 0,0), the same
# [x, y]; VCLR 33 x 33 RGB, white = untinted.
VHGT_DELTA_MAX = 127
VNML_SCALE = 127
# Texture layers: four quadrants of 17 x 17 vertices (Mutagen Quadrant BottomLeft, BottomRight, TopLeft, TopRight
# = SW, SE, NW, NE); a VTXT position is x + 17 * y within the quadrant (shared quadrant edges agree to 0.003 mean
# opacity over 3,157 vanilla cells read this way, 0.22 the other way); at most LAND_QUADRANT_LAYERS alpha layers
# over one base layer per quadrant (vanilla's maximum, measured: 6).
QUADRANT_VERTS = QUADS_PER_CELL // 2 + 1  # 17
QUADRANTS = ("BottomLeft", "BottomRight", "TopLeft", "TopRight")


def province_to_skyrim(x_m: float, y_south_m: float) -> tuple[float, float]:
    """An imported province position (x east, y south from the north-west corner, metres) as Skyrim units."""
    x0, y0 = PROVINCE_CELL_SW
    span = (PROVINCE_SAMPLES - 1) * VERTEX_SPACING_UNITS
    x = x0 * CELL_UNITS + x_m / PROVINCE_SAMPLE_M * VERTEX_SPACING_UNITS
    y = y0 * CELL_UNITS + span - y_south_m / PROVINCE_SAMPLE_M * VERTEX_SPACING_UNITS
    return x, y


def height_to_steps(z_m):
    """Metres above sea (scalar or numpy array) as VHGT steps, unrounded."""
    return z_m * (UNITS_PER_METRE / VHGT_STEP_UNITS)

# Condition tabs of each value perk entry point the combat wiring uses (CK: Perk Owner first; 1.6-wiring). The
# entry point's tab count is written into the PERK effect; a wrong count is refused by the CK, so the L4 drafts read
# each entry's effect in game (tests/journeys/fight-damage-builds.yaml).
PERK_ENTRY_TABS = {"ModAttackDamage": 3, "ModIncomingDamage": 3, "ModPowerAttackStamina": 2, "ModPercentBlocked": 3,
                   "ModIncomingStagger": 2, "ModTargetStagger": 2}
# Skyrim's NPC_ height and weight the archetype records are written with (the CK's defaults for a new actor).
NPC_DEFAULT_HEIGHT = 1.0
NPC_DEFAULT_WEIGHT = 50.0
