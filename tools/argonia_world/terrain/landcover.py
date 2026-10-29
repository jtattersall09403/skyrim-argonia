"""Land-cover classes and the vanilla LTEX forms that paint them (decision 0028; old 0011's micro layer).

The land-cover raster (`landcover-i16.npy`, the old chain's ground-control red channel at the heightfield's
resolution) stores one class id per sample. Each class paints one vanilla landscape texture (LTEX) of
Skyrim.esm that Tropical Skyrim replaces in place, so the player's Tropical Skyrim install supplies the texture
and the grass that texture carries (LTEX.GNAM); we reference the form and ship nothing (0003). No snow, ice or
glacier form is used (0012). The classes and the mapping are world data: their home is the `land_cover` and
`land_cover_ltex` tables (the schema's 2.W1 block); `SEED` below is what the 2.W1 lane first wrote there
and what a test checks the tables against, never a second source the build reads.

Evidence (2026-10-29, docs/research/journals/terrain.md): the 68 LTEX of Skyrim.esm dumped with their TXST
diffuse paths; Tropical Skyrim (vault copy of 33017, the LE release; SE 78044 to re-check when 0.2 syncs it)
ships a replacement for 66 of them (all but LMineFloorDirt01 and LScrub01). Class names from
`flora/groundcover.json` byLandCover; ids 4, 25, 30 and 36 are its four `bare` covers, identified by their
measured height, slope and wetness.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Cover:
    id: int
    name: str
    bare: bool  # carries no groundcover in the old system
    ltex: str  # FormKey of the vanilla LTEX
    ltex_edid: str
    why: str


# id, name, bare, LTEX FormKey, LTEX EditorID, why that texture
SEED: tuple[Cover, ...] = tuple(Cover(*r) for r in (
    (0, "SILT", False, "0132E9:Skyrim.esm", "LRiverMud01", "wet fine sediment at the waterline; river mud with water kelp"),
    (1, "RIVER_MUD", False, "0132E9:Skyrim.esm", "LRiverMud01", "the channel bed"),
    (2, "BANK_WET", False, "01301F:Skyrim.esm", "LRiverbedEdge01", "the wet bank grade between bed and ground"),
    (3, "SCUM", False, "0132E9:Skyrim.esm", "LRiverMud01", "stagnant water over mud (73% under water)"),
    (4, "BLACK_MUD", True, "098E6C:Skyrim.esm", "LRiverMud01NoGrass", "the wettest black mud, bare"),
    (5, "PUDDLE", False, "098E6C:Skyrim.esm", "LRiverMud01NoGrass", "pooled water on mud"),
    (6, "CLAY", False, "021711:Skyrim.esm", "LReachDirt01", "red-brown clay banks"),
    (7, "MUCK", False, "075069:Skyrim.esm", "LFrozenMarshLichen01", "marsh muck; the marsh family Tropical Skyrim turns to swamp"),
    (8, "BC_MUD", False, "075069:Skyrim.esm", "LFrozenMarshLichen01", "Bitter Coast style mud flat"),
    (9, "PEAT", False, "057DCF:Skyrim.esm", "LFallForestDirt01", "dark peat ground"),
    (10, "MUD_LEAVES", False, "057DC7:Skyrim.esm", "LFallForestLeaves01", "mud under leaf fall"),
    (11, "MARSH_GRASS", False, "075067:Skyrim.esm", "LFrozenMarshGrass01", "marsh grass"),
    (12, "UNDERGROWTH", False, "013876:Skyrim.esm", "LPineForest03", "forest floor with ferns"),
    (13, "BC_MOSS", False, "01CC43:Skyrim.esm", "LReachMoss01", "moss mat"),
    (14, "MOSS", False, "01CC43:Skyrim.esm", "LReachMoss01", "moss mat"),
    (15, "SWAMP_GRASS", False, "075067:Skyrim.esm", "LFrozenMarshGrass01", "swamp grass"),
    (16, "TROP_GRASS", False, "01342A:Skyrim.esm", "LFieldGrass02", "open tropical grass"),
    (17, "GRASS_DIRT", False, "013428:Skyrim.esm", "LFieldGrass01", "grass over dirt"),
    (18, "SCRUB", False, "024E30:Skyrim.esm", "LTundra01", "scrubland"),
    (19, "JUNGLE", False, "0137CC:Skyrim.esm", "LPineForest02", "jungle floor with forest grass and fern"),
    (20, "FOREST_FLOOR", False, "058606:Skyrim.esm", "LFallForestGrass01", "forest floor"),
    (21, "LITTER", False, "057DC7:Skyrim.esm", "LFallForestLeaves01", "leaf litter"),
    (23, "BC_ROCK", False, "01CC45:Skyrim.esm", "LReachMossyRocks01", "mossy rock"),
    (24, "SAND", False, "06B3CF:Skyrim.esm", "LCoastBeach01", "inland sand"),
    (25, "SALT", True, "06B3D1:Skyrim.esm", "LCoastBeach02", "salt pan, bare and pale"),
    (26, "DRY_CLAY", False, "021711:Skyrim.esm", "LReachDirt01", "dry clay"),
    (27, "PATH", False, "0B424C:Skyrim.esm", "LDirtPath01", "a worn path"),
    (28, "PEAT_SLOPE", False, "075070:Skyrim.esm", "LFrozenMarshDirtSlopes01", "peat on a slope"),
    (29, "TRACK", False, "000C16:Skyrim.esm", "LDirt02", "a churned track"),
    (30, "BC_ROAD", True, "0B424C:Skyrim.esm", "LDirtPath01", "the built road until 2.W3's road surface"),
    (31, "MOUNTAIN_ROCK", False, "000AE4:Skyrim.esm", "LRocks01", "upland rock"),
    (32, "BEACH_SAND", False, "06DD55:Skyrim.esm", "LCoastBeachGrass01", "beach with beach grass"),
    (33, "SEABED_SAND", False, "06B3CF:Skyrim.esm", "LCoastBeach01", "shallow sea sand"),
    (34, "PEBBLES", False, "013184:Skyrim.esm", "LRiverBottom01", "pebble beds of upland streams"),
    (35, "OCEAN_FLOOR", False, "06B4C6:Skyrim.esm", "LCoastOceanFloor01", "the sea floor with kelp and coral"),
    (36, "DIRT_CLIFF", True, "000C14:Skyrim.esm", "LDirt01", "steep bare dirt"),
    (37, "SCREE", False, "02C6C6:Skyrim.esm", "LTundraRocks01", "scree"),
))

# The LTEX forms Tropical Skyrim replaces, by EditorID (the 66 of Skyrim.esm's 68; measured, see the docstring).
NOT_REPLACED_BY_TS = frozenset({"LMineFloorDirt01", "LScrub01"})


def table(world=None) -> dict[int, Cover]:
    """The classes by id: the database's rows when its tables hold them, else SEED (before the first write)."""
    if world is not None and "land_cover_ltex" in getattr(world, "tables", {}):
        rows = world.query(
            "SELECT c.id, c.name, c.bare, m.ltex_form_key, m.ltex_edid, m.why FROM land_cover c "
            "JOIN land_cover_ltex m ON m.land_cover_id = c.id ORDER BY c.id")
        if rows:
            return {r[0]: Cover(r[0], r[1], bool(r[2]), r[3], r[4], r[5]) for r in rows}
    return {c.id: c for c in SEED}


def seed_rows() -> tuple[list[dict], list[dict]]:
    covers = [{"id": c.id, "name": c.name, "bare": c.bare} for c in SEED]
    maps = [{"land_cover_id": c.id, "ltex_form_key": c.ltex, "ltex_edid": c.ltex_edid,
             "tropical_skyrim_replaces": c.ltex_edid not in NOT_REPLACED_BY_TS, "why": c.why} for c in SEED]
    return covers, maps


# Apron classes (beyond the border, where no land-cover raster exists): the province's rule on height and slope
# only (old 0067 §4), as the ids above.
def apron_class(height_m, slope_deg):
    """Vectorised: numpy arrays of height (m) and slope (degrees) -> class ids."""
    import numpy as np

    c = np.full(np.shape(height_m), 17, dtype=np.int16)  # GRASS_DIRT
    c = np.where(height_m < 30, 15, c)  # SWAMP_GRASS on the low ground
    c = np.where(height_m > 120, 18, c)  # SCRUB on the hills
    c = np.where(slope_deg > 28, 36, c)  # DIRT_CLIFF
    c = np.where((slope_deg > 34) | (height_m > 220), 31, c)  # MOUNTAIN_ROCK
    c = np.where(height_m < 1.5, 32, c)  # BEACH_SAND
    c = np.where(height_m < -0.5, 33, c)  # SEABED_SAND
    c = np.where(height_m < -4.0, 35, c)  # OCEAN_FLOOR
    return c.astype(np.int16)
