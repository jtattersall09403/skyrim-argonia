"""Per-cell water type and region (nw-02 step 7), from the landcover.

    python3 -m tools.newworld.world.cells [--out out/newworld/plugin]

Writes `<out>/cells.json` ({"build_id", "cells": {"cx,cy": {"water": watr key, "region": region id}}, "watr": the
water records by key, "regions": name and wetness per region, "limits": what the engine cannot show}). The low mist
refs are world/mist.py's; the regions' weathers are tools/newworld/atmosphere.py's.

Placed refs hook (shared with the placement step): every producer writes `<out>/refs/<producer>/cy<+NNN>.jsonl`,
one JSON object per line: {"base": "<plugin>:<editor id>", "x", "y", "z" (world units), "rx", "ry", "rz"
(radians), "scale"}; the writer (`ArgoniaPlugin newworld write`) places each in the exterior cell holding (x, y),
linking the base when it is in an allowed master and copying it as our own record otherwise (ForeignCopy.cs).

Water (research/nw-02-ground-water-rules.md section 3.4; one level 0, so the type is chosen per cell, XCWT): the
cell's type is its dominant water body's kind (by water samples). Sea, bay and lake: the world water `DefaultWater`
(Update.esm's, the stack's winner); green marsh `DefaultMarshWater`; black swamp `MurkyWater` (BM&V's own world
water); estuary Update.esm's `DefaultWaterFlowBlend` (blends a river into the sea; the sea's colours); pond `DefaultCreekWater` (clear);
rivers `RiverWaterFlowNE/NW/SE` by the body's flow direction and our mirrored copy for SW; streams
`CreekWaterFlowSE/SW` and our mirrored NE/NW copies. Records our own are `{"copy": source, "velocity": [x, y]}`.

"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

from tools.newworld import frame as f
from tools.newworld import landcover as lc

REPO = Path(__file__).resolve().parents[3]
LC = REPO / "out/newworld/landcover"
SAMPLE = 128.0
VEL = {"NE": (2.54, 1.35), "NW": (-1.96, 2.0), "SE": (1.8, -2.2), "SW": (-1.8, -2.2)}
CREEK = {"SE": (0.70, -0.72), "SW": (-0.98, -0.70), "NE": (0.70, 0.72), "NW": (-0.98, 0.70)}
WATR = {
    "sea": {"link": "Skyrim.esm:DefaultWater"},
    "green-marsh": {"link": "Skyrim.esm:DefaultMarshWater"},
    "blackwater-swamp": {"link": "Skyrim.esm:MurkyWater"},
    "estuary": {"link": "Update.esm:DefaultWaterFlowBlend"},
    "pond": {"link": "Skyrim.esm:DefaultCreekWater"},
    "river-NE": {"link": "Skyrim.esm:RiverWaterFlowNE"}, "river-NW": {"link": "Skyrim.esm:RiverWaterFlowNW"},
    "river-SE": {"link": "Skyrim.esm:RiverWaterFlowSE"},
    "river-SW": {"copy": "Skyrim.esm:RiverWaterFlowSE", "edid": "ANW_RiverWaterFlowSW", "velocity": VEL["SW"]},
    "stream-SE": {"link": "Skyrim.esm:CreekWaterFlowSE"}, "stream-SW": {"link": "Skyrim.esm:CreekWaterFlowSW"},
    "stream-NE": {"copy": "Skyrim.esm:CreekWaterFlowSE", "edid": "ANW_CreekWaterFlowNE", "velocity": CREEK["NE"]},
    "stream-NW": {"copy": "Skyrim.esm:CreekWaterFlowSW", "edid": "ANW_CreekWaterFlowNW", "velocity": CREEK["NW"]},
}
KIND_WATR = {"ocean": "sea", "shallow-coast": "sea", "bay": "sea", "lake": "sea", "green-marsh": "green-marsh",
             "blackwater-swamp": "blackwater-swamp", "estuary": "estuary", "pond": "pond"}
LIMITS = [
    "No flowmaps: river and stream cells flow by their type's fixed vector only (no per-cell flow texture), one of "
    "four directions per cell; rivers that bend change type cell by cell.",
    "One water type per cell: a cell holding two kinds shows its dominant kind's water.",
    "Adjacent cells of different types are graded: a cell near a change of type is our own blend record (ArgoniaPlugin WaterBlend.cs).",
    "No rapids, falls or ripple FX statics yet (placement step).",
    "Region map names need REGN area polygons for the world map; regions are linked per cell (XCLR) for weather.",
]


def log(*a):
    print(*a, file=sys.stderr, flush=True)


def octant(deg: float) -> str:
    d = deg % 360
    return "NE" if d < 90 else "SE" if d < 180 else "SW" if d < 270 else "NW"


def build(out: Path) -> dict:
    man = json.loads((out / "land/manifest.json").read_text())
    legend = json.loads((LC / "legend.json").read_text())
    if legend["build_id"] != man["build_id"]:
        raise RuntimeError("landcover is another terrain build: rerun landcover")
    g = man["grid"]
    reg = np.load(LC / "region.npy", mmap_mode="r")
    kind = np.load(LC / "kind.npy", mmap_mode="r")
    flags = np.load(LC / "flags.npy", mmap_mode="r")
    kinds, regions = legend["kinds"], legend["regions"]
    flow = {tuple(c["cell"]): float(c["flow_deg"]) for c in json.loads((f.OUT / "water_flow_cells.json").read_text())
            if c.get("flow_deg") is not None}  # tools/newworld/water_kinds.py: cells where water flows
    from tools.newworld.water_kinds import region_character
    still = region_character()
    cells, counts = {}, Counter()
    for cy in range(g["cy_top"], g["cy_bottom"] - 1, -1):
        north = (g["cy_top"] - cy) * 32
        sl_r = slice(north, north + 33)
        FL = np.asarray(flags[sl_r]); K = np.asarray(kind[sl_r]); R = np.asarray(reg[sl_r])
        for i in range(g["cells_x"]):
            cx = g["cx0"] + i
            sc = slice(i * 32, i * 32 + 33)
            w = (FL[:, sc] & 1) == 1
            rc = Counter(R[:, sc].ravel().tolist()).most_common(1)[0][0]
            rec = {"region": regions[rc]}
            if w.any():
                kc = Counter(K[:, sc][w].tolist()).most_common(1)[0][0]
                kname = kinds[kc] if kc < len(kinds) else "ocean"
                if kname in ("river", "stream") and (cx, cy) in flow:  # flowing here: the cell's mean flow direction
                    key = f"{kname}-{octant(flow[(cx, cy)])}"
                elif kname in ("river", "stream"):  # a channel that does not flow in this cell: the region's still water
                    key = KIND_WATR[still.get(regions[rc], {}).get("wet", "pond")]
                else:
                    key = KIND_WATR.get(kname, "sea")
                rec["water"] = key
                counts[key] += 1
            cells[f"{cx},{cy}"] = rec
    region_rows = {}
    for r in lc.jsonl("region"):
        wv = float(r.get("wetness") or 0.5)
        region_rows[r["id"]] = {"name": r["name"], "map_label": r.get("map_label"), "wetness": wv}
    res = {"build_id": man["build_id"], "cells": cells, "watr": WATR, "regions": region_rows, "limits": LIMITS,
           "water_cells": dict(counts)}
    (out / "cells.json").write_text(json.dumps(res))
    log(f"cells: water types {dict(counts)}")
    return res


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=REPO / "out/newworld/plugin")
    build(ap.parse_args(argv).out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
