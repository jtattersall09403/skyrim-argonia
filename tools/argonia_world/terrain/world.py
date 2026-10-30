"""The WRLD intermediate for ArgoniaWorld.esm (decision 0031; ArgoniaGen's LandWorld.cs reads it).

ArgoniaWorld.esm's ids are computed, never allocated: the plugin is generated whole from the grid, so a cell's
FormID is a function of its grid position (build.Builder.keys) from CELLS_FIRST, and the two records below take
the first ids of the plugin's range. Argonia.esm, which has ArgoniaWorld.esm as a master, overrides the WRLD to
set what its own records supply (climate, music, water: decision 0031 §2; ArgoniaWorld.esm cannot link to its
dependant).

    {"schema": 1, "mod": "ArgoniaWorld.esm", "author", "description", "loadOrder": [...],
     "records": [{"type": "WRLD", "formKey", "edid", "name", "defaultLandHeight", "defaultWaterHeight" (units),
                  "boundsMin", "boundsMax" (cells), "map": {"usable", "nw", "se", "cameraMin", "cameraMax",
                  "cameraPitch"}, "topCell": {"formKey"}}],
     "land": the shard directory build.py wrote,
     "regions": [{"type": "REGN", "formKey", "edid"}] the shells, "cellRegions": [{"cy", "cx0", "cx1", "region"}]}
"""
from __future__ import annotations

import json
from pathlib import Path

from tools.argonia_world import skyrim_units as su
from tools.argonia_world.terrain.build import LAND_PLUGIN, form_key

WRLD_ID = su.FORMID_FIRST  # the plugin's first id
TOP_CELL_ID = su.FORMID_FIRST + 1  # the worldspace's persistent cell
CELLS_FIRST = su.FORMID_FIRST + 0x10  # build.Builder's default base: CELL, LAND pairs by grid position
EDID = "ARG_Province"
NAME = "Black Marsh"  # the worldspace's name the map shows (immersion inventory: our word)
DEFAULT_LAND_UNITS = -2048.0  # a cell with no LAND (open sea beyond the apron) lies 29 m under the sea
DEFAULT_WATER_UNITS = 0.0  # the sea at 0 (brief §a)
MAP_CAMERA = (50000.0, 80000.0, 50.0)  # min, max height and pitch: Skyrim.esm Tamriel's values (measured)
LOAD_ORDER = ["Skyrim.esm", "Dawnguard.esm"]  # the LTEX forms are Skyrim.esm's (decision 0028); the water's falls piece is Dawnguard's (2.W2)
# The gate's fixed sample (decision 0031 §3): the steepest sea cliff (-19, 58), the south-west corner across the
# border into the apron, six-layer ground in the middle, and the Tear road's gate cell on the north border.
SAMPLE = ((-20, 57, -19, 58), (-63, -63, -62, -62), (0, 0, 1, 1), (-12, 63, -11, 64))
MANIFEST = Path(__file__).with_name("sample-manifest.json")  # the sample's ESM sha256, committed


def wrld(cell_range: tuple[int, int, int, int]) -> dict:
    x0, y0, x1, y1 = cell_range
    px0, py0 = su.PROVINCE_CELL_SW
    px1, py1 = px0 + su.PROVINCE_CELLS - 1, py0 + su.PROVINCE_CELLS - 1
    return {
        "type": "WRLD", "formKey": form_key(WRLD_ID, 0, LAND_PLUGIN), "edid": EDID, "name": NAME,
        "defaultLandHeight": DEFAULT_LAND_UNITS, "defaultWaterHeight": DEFAULT_WATER_UNITS,
        "boundsMin": [float(x0), float(y0)], "boundsMax": [float(x1), float(y1)],
        "map": {"usable": [0, 0], "nw": [px0, py1], "se": [px1, py0], "cameraMin": MAP_CAMERA[0],
                "cameraMax": MAP_CAMERA[1], "cameraPitch": MAP_CAMERA[2]},
        "topCell": {"formKey": form_key(TOP_CELL_ID, 0, LAND_PLUGIN)},
    }


def document(cell_range: tuple[int, int, int, int], land_dir: Path, world=None) -> dict:
    """The WRLD intermediate, the REGN shells and the cells' region runs (XCLR; 2.W3's regions/api.py)."""
    from tools.argonia_world import db
    from tools.argonia_world.regions import api as regions

    w = world if world is not None else db.open()
    return {"schema": 1, "mod": LAND_PLUGIN, "author": "Elder Souls: Argonia",
            "description": "The generated ground of Black Marsh: the worldspace, every exterior cell and its LAND "
                           "(decision 0031). Built, never edited.",
            "loadOrder": LOAD_ORDER, "records": [wrld(cell_range)], "land": str(land_dir),
            "regions": regions.shell_records(w), "cellRegions": regions.cell_region_runs(w)}


def write(path: Path, cell_range: tuple[int, int, int, int], land_dir: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document(cell_range, land_dir), indent=1, sort_keys=True) + "\n")
    return path
