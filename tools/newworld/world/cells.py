"""Per-cell water type and region, and the ground mist refs (nw-02 steps 7 and 9), from the landcover.

    python3 -m tools.newworld.world.cells [--out out/newworld/plugin]

Writes `<out>/cells.json` ({"build_id", "cells": {"cx,cy": {"water": watr key, "region": region id}}, "watr": the
water records by key, "regions": weather mix per region, "limits": what the engine cannot show}) and the mist refs,
`<out>/refs/mist/cy<+NNN>.jsonl`.

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

Mist (section 5.2, Morthal): `FXMistLow01HalfVis` 60%, `FXMistLow01LongHalfVis` 30%, `FXMistLow01Long` 10%, a
jittered 50 m lattice (400 per km2 at full density) over marsh and swamp habitats, still inland water, and land
within 20 m of still inland water; accepted with the region's wetness (0.35 + 0.65 wetness) times the habitat's
weight; centre +0.6 to +1.0 m over the ground or water (below eye level), scale 1.3 to 1.6, random yaw.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter
from pathlib import Path

import numpy as np
from scipy import ndimage as ndi

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
# BlackMarshClimate's mix (Fog 45, OvercastRain 20, StormRain 20, Cloudy 10, Clear 5), wetter and foggier in the marsh
WEATHERS = ("SkyrimFog", "SkyrimOvercastRain", "SkyrimStormRain", "SkyrimCloudy", "SkyrimClear")
MIX_WET = (55, 18, 15, 8, 4)
MIX_MID = (45, 20, 20, 10, 5)
MIX_DRY = (30, 18, 15, 17, 20)
MIST_HAB = {"reed_marsh": 1.0, "cypress_swamp": 1.0, "drowned_forest": 1.0, "mangrove_fringe": 0.7,
            "open_still_water": 1.0, "swamp_hummock": 0.45, "hist_grove": 0.5, "lake_bed": 0.5}
MIST_KINDS = ("pond", "green-marsh", "blackwater-swamp", "lake")
MIST_TYPES = (("FXMistLow01HalfVis", 0.6), ("FXMistLow01LongHalfVis", 0.3), ("FXMistLow01Long", 0.1))
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
    hab = np.load(LC / "habitat.npy", mmap_mode="r")
    reg = np.load(LC / "region.npy", mmap_mode="r")
    kind = np.load(LC / "kind.npy", mmap_mode="r")
    flags = np.load(LC / "flags.npy", mmap_mode="r")
    shore = np.load(LC / "shore.npy", mmap_mode="r")
    hm = np.load(man["heightmap"], mmap_mode="r")
    habs, kinds, regions = legend["habitats"], legend["kinds"], legend["regions"]
    ox, oy = legend["origin_world"]
    wet = {r["id"]: float(r.get("wetness") or 0.5) for r in lc.jsonl("region")}
    rng = np.random.default_rng(5150)
    flow = {tuple(c["cell"]): float(c["flow_deg"]) for c in json.loads((f.OUT / "water_flow_cells.json").read_text())
            if c.get("flow_deg") is not None}  # tools/newworld/water_kinds.py: cells where water flows
    from tools.newworld.water_kinds import region_character
    still = region_character()
    cells, counts = {}, Counter()
    mist_hab = np.zeros(len(habs), np.float32)
    for h, v in MIST_HAB.items():
        mist_hab[habs.index(h)] = v
    mist_kind = np.isin(np.arange(256), [kinds.index(k) for k in MIST_KINDS])
    refs_dir = out / "refs/mist"
    refs_dir.mkdir(parents=True, exist_ok=True)
    for old in refs_dir.glob("*.jsonl"):
        old.unlink()
    nmist = Counter()
    lat = 50 * 70 / SAMPLE  # mist lattice, samples
    for cy in range(g["cy_top"], g["cy_bottom"] - 1, -1):
        north = (g["cy_top"] - cy) * 32
        sl_r = slice(north, north + 33)
        H_ = np.asarray(hm[sl_r]); FL = np.asarray(flags[sl_r]); K = np.asarray(kind[sl_r]); R = np.asarray(reg[sl_r])
        HB = np.asarray(hab[sl_r]); SH = np.asarray(shore[sl_r]).astype(np.float32) / 10
        lines = []
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
            # mist
            wr = wet.get(regions[rc], 0.5)
            dens = mist_hab[HB[:, sc]]
            near_still = (~w) & (SH[:, sc] < 20) & mist_kind[K[:, sc]]
            dens = np.maximum(dens, np.where(near_still | (w & mist_kind[K[:, sc]]), 1.0, 0)) * (0.35 + 0.65 * wr)
            dens[(w & ~mist_kind[K[:, sc]])] = 0  # not over running water or the sea
            if rec.get("water") == "sea":
                dens[ndi.binary_dilation(w, iterations=3)] = 0  # a sea cell's water carries none, nor its edge
            n = 32 / lat
            for a in range(int(math.ceil(n))):
                for b in range(int(math.ceil(n))):
                    ry = (a + rng.random()) * lat; rx = (b + rng.random()) * lat
                    if ry > 32 or rx > 32:
                        continue
                    yi, xi = int(ry), int(rx)
                    if rng.random() >= dens[yi, xi] * min(1.0, (n * n) / (32 / lat) ** 2):
                        continue
                    t = rng.choice(len(MIST_TYPES), p=[p for _, p in MIST_TYPES])
                    gz = max(float(H_[yi, xi + i * 32]), 0.0)
                    x = ox + (i * 32 + rx) * SAMPLE; y = oy - (north + ry) * SAMPLE
                    z = gz + rng.uniform(0.6, 1.0) * 70
                    lines.append(json.dumps({"base": f"Skyrim.esm:{MIST_TYPES[t][0]}", "x": round(x, 1), "y": round(y, 1),
                                             "z": round(z, 1), "rx": 0, "ry": 0, "rz": round(rng.uniform(0, 2 * math.pi), 3),
                                             "scale": round(rng.uniform(1.3, 1.6), 2)}))
                    nmist[regions[rc]] += 1
        (refs_dir / f"cy{cy:+04d}.jsonl").write_text("\n".join(lines) + ("\n" if lines else ""))
    region_rows = {}
    for r in lc.jsonl("region"):
        wv = float(r.get("wetness") or 0.5)
        mix = MIX_WET if wv >= 0.8 else MIX_DRY if wv < 0.55 else MIX_MID
        region_rows[r["id"]] = {"name": r["name"], "map_label": r.get("map_label"), "wetness": wv,
                                "weathers": dict(zip(WEATHERS, mix)), "mist_refs": nmist.get(r["id"], 0)}
    res = {"build_id": man["build_id"], "cells": cells, "watr": WATR, "regions": region_rows, "limits": LIMITS,
           "water_cells": dict(counts), "mist_refs": int(sum(nmist.values()))}
    (out / "cells.json").write_text(json.dumps(res))
    log(f"cells: water types {dict(counts)}; mist refs {sum(nmist.values())}")
    return res


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=REPO / "out/newworld/plugin")
    build(ap.parse_args(argv).out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
