"""The low mist refs (walk 5): Hjaalmarch's way, denser and stronger where the region's atmosphere class asks.

    python3 -m tools.newworld.world.mist [--out out/newworld/plugin]

Writes `<out>/refs/mist/cy<+NNN>.jsonl` in the placed-refs hook (world/cells.py's format), one file per cell row,
each row seeded on its own (a rerun rewrites the same refs). Reads the landcover rasters, the cells' water types
(`<out>/cells.json`, so run after world/cells.py) and each region's class (the database, region_atmosphere).

Measured in Hjaalmarch (docs/research/nw-02-walk5-atmosphere.md section 3.5): over its DefaultMarshWater cells 3.53
mist refs a hectare, at most 5 in a cell, 58 % over water; the FXMistLow family, 43 % of them full-opacity
(`FXMistLow01`, `FXMistLow01Long`), the rest half (`...HalfVis`); within each opacity the long mesh 57 % (full) and 59 %
(half); the centre 1.3 / 1.8 / 2.7 m (p10/50/90) over the water; scale 1.0 / 1.45 / 1.9. Always on, no script.

Ours: a jittered 25 m lattice (16 sites a hectare); a site is kept with the chance density x Hjaalmarch's 3.53 / 16,
where the density (a multiple of Hjaalmarch's) is the region's class density (classes.json: blackwater swamp 2.2,
green marsh 2.0, ... island 0.4) times the site's weight, raised to the water's own floor over blackwater swamp (2.0),
green marsh (1.8) and pond (1.2) water and on land within 20 m of it (0.8 of the floor), so those waters carry their
mist whatever region they lie in. Weight 1 over still water and on marsh and swamp habitats, 0.8 on land within 20 m
of still water, the habitat's own weight elsewhere (mangrove 0.7, hummock 0.45, Hist grove 0.5), 0.25 over flowing
water (river fog), 0 over the sea, bays and lakes (a cell typed sea carries none on its water nor within 3 samples of
it). The class also sets the full-opacity share and the scale. The centre sits 0.9 to 1.4 m over the water or the
ground under the ref (bilinear on the heightmap, as the LAND is read): below eye level, and high enough that most of
the 2.5 m mesh stands above the surface. A cell takes at most CAP mist refs and never more than the placer's budget
(REFS_CAP natural plus mist refs) leaves after the cell's flora refs (`<out>/refs/flora/`).
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

from tools.newworld import atmosphere

REPO = Path(__file__).resolve().parents[3]
LC = REPO / "out/newworld/landcover"
SAMPLE = 128.0           # units per landcover sample
CELL_HA = (4096 / 70) ** 2 / 1e4   # a cell: 0.342 ha
HJAAL_PER_HA = 3.53      # Hjaalmarch's marsh-water cells (section 3.5)
HJAAL_MAX_CELL = 5
LATTICE_M = 25.0
CAP = 8                  # refs in one cell
REFS_CAP = 162           # natural plus mist refs in a cell: vanilla's forested max (place.py CAP)
WATER_MIN = 1.4          # mist refs a hectare over blackwater swamp and green marsh water, x Hjaalmarch's
LIFT_RANGE = (0.5, 2.0)  # every ref's centre over its water or ground, metres
Z_M = (0.9, 1.4)         # centre over the water or ground, metres
HAB_W = {"reed_marsh": 1.0, "cypress_swamp": 1.0, "drowned_forest": 1.0, "mangrove_fringe": 0.7,
         "open_still_water": 1.0, "swamp_hummock": 0.45, "hist_grove": 0.5, "lake_bed": 0.5}
STILL = ("pond", "green-marsh", "blackwater-swamp")
FLOWING = ("river", "stream", "estuary")
NEAR_STILL_M, NEAR_W, FLOW_W = 20.0, 0.8, 0.25
KIND_FLOOR = {"blackwater-swamp": 2.0, "green-marsh": 1.8, "pond": 1.2}   # x Hjaalmarch, over the water and its banks
FULL = (("FXMistLow01Long", 0.57), ("FXMistLow01", 0.43))
HALF = (("FXMistLow01LongHalfVis", 0.59), ("FXMistLow01HalfVis", 0.41))


def log(*a):
    print(*a, file=sys.stderr, flush=True)


def per_site(density):
    """The chance a site is kept, for a density (multiple of Hjaalmarch's)."""
    return np.minimum(1.0, density * HJAAL_PER_HA / (1e4 / LATTICE_M ** 2))


def build(out: Path) -> dict:
    man = json.loads((out / "land/manifest.json").read_text())
    legend = json.loads((LC / "legend.json").read_text())
    if legend["build_id"] != man["build_id"]:
        raise RuntimeError("landcover is another terrain build: rerun landcover")
    cj = json.loads((out / "cells.json").read_text())
    if cj["build_id"] != man["build_id"]:
        raise RuntimeError("cells.json is another terrain build: rerun world/cells.py")
    g = man["grid"]
    hab = np.load(LC / "habitat.npy", mmap_mode="r")
    kind = np.load(LC / "kind.npy", mmap_mode="r")
    flags = np.load(LC / "flags.npy", mmap_mode="r")
    shore = np.load(LC / "shore.npy", mmap_mode="r")
    hm = np.load(man["heightmap"], mmap_mode="r")
    habs, kinds = legend["habitats"], legend["kinds"]
    ox, oy = legend["origin_world"]
    cls, _ = atmosphere.load_sources()
    rc = atmosphere.region_classes()
    hab_w = np.zeros(len(habs), np.float32)
    for h, v in HAB_W.items():
        hab_w[habs.index(h)] = v
    still = np.isin(np.arange(256), [kinds.index(k) for k in STILL if k in kinds])
    flowing = np.isin(np.arange(256), [kinds.index(k) for k in FLOWING if k in kinds])
    floor = np.zeros(256, np.float32)
    for k, v in KIND_FLOOR.items():
        floor[kinds.index(k)] = v
    refs_dir = out / "refs/mist"
    refs_dir.mkdir(parents=True, exist_ok=True)
    for old in refs_dir.glob("*.jsonl"):
        old.unlink()
    lat = LATTICE_M * 70 / SAMPLE   # lattice, samples
    natural = flora_counts(out / "refs/flora")
    n = int(math.ceil(32 / lat))
    by_region, by_class = Counter(), Counter()
    for cy in range(g["cy_top"], g["cy_bottom"] - 1, -1):
        rng = np.random.default_rng((5150, cy - g["cy_bottom"]))
        north = (g["cy_top"] - cy) * 32
        sl_r = slice(north, north + 33)
        H_ = np.asarray(hm[sl_r]); FL = np.asarray(flags[sl_r]); K = np.asarray(kind[sl_r])
        HB = np.asarray(hab[sl_r]); SH = np.asarray(shore[sl_r]).astype(np.float32) / 10
        lines = []
        for i in range(g["cells_x"]):
            cx = g["cx0"] + i
            cell = cj["cells"].get(f"{cx},{cy}")
            if not cell:
                continue
            cid, _band = rc.get(cell["region"], (None, None))
            if cid is None:
                continue
            c = cls["classes"][cid]["mist"]
            sc = slice(i * 32, i * 32 + 33)
            w = (FL[:, sc] & 1) == 1
            k = K[:, sc]
            wt = hab_w[HB[:, sc]]
            wt = np.where(w & still[k], 1.0, wt)
            wt = np.where(~w & (SH[:, sc] < NEAR_STILL_M) & still[k], np.maximum(wt, NEAR_W), wt)
            wt = np.where(w & flowing[k], FLOW_W, wt)
            wt[w & ~still[k] & ~flowing[k]] = 0  # the sea, bays and lakes
            near = still[k] & (w | (SH[:, sc] < NEAR_STILL_M))
            p = per_site(np.where(near, np.maximum(c["density"] * wt, floor[k] * np.where(w, 1.0, NEAR_W)), c["density"] * wt))
            p[w & ~still[k] & ~flowing[k]] = 0  # the sea, bays and lakes
            if cell.get("water") == "sea":
                p[ndi.binary_dilation(w, iterations=3)] = 0
            placed, cap = 0, max(0, min(CAP, REFS_CAP - natural.get((cx, cy), 0)))
            for a in range(n):
                for b in range(n):
                    ry, rx = (a + rng.random()) * lat, (b + rng.random()) * lat
                    u = rng.random()
                    if ry > 32 or rx > 32 or placed >= cap:
                        continue
                    yi, xi = int(ry), int(rx)
                    if u >= p[yi, xi]:
                        continue
                    full = rng.random() < c["full_vis"]
                    names, probs = zip(*(FULL if full else HALF))
                    base = names[int(rng.choice(len(names), p=probs))]
                    surf = max(ground(H_, ry, rx + i * 32), 0.0)
                    lines.append(json.dumps({"base": f"Skyrim.esm:{base}", "x": round(ox + (i * 32 + rx) * SAMPLE, 1),
                                             "y": round(oy - (north + ry) * SAMPLE, 1), "z": round(surf + rng.uniform(*Z_M) * 70, 1),
                                             "rx": 0, "ry": 0, "rz": round(rng.uniform(0, 2 * math.pi), 3),
                                             "scale": round(rng.uniform(*c["scale"]), 2)}))
                    placed += 1
            by_region[cell["region"]] += placed
            by_class[cid] += placed
        (refs_dir / f"cy{cy:+04d}.jsonl").write_text("\n".join(lines) + ("\n" if lines else ""))
    res = {"build_id": man["build_id"], "refs": int(sum(by_region.values())), "by_region": dict(by_region), "by_class": dict(by_class)}
    (refs_dir / "manifest.json").write_text(json.dumps(res, indent=1))
    log(f"mist: {res['refs']} refs; by class {dict(by_class)}")
    return res


def ground(h, ry: float, rx: float) -> float:
    """The ground at a fractional sample position (row south from the slice's top, column), bilinear on the samples,
    as the game reads its LAND (NewWorldAtmosphere.cs MistStudy, NewWorldVerify.cs)."""
    j, i = min(int(ry), h.shape[0] - 2), min(int(rx), h.shape[1] - 2)
    ay, ax = ry - j, rx - i
    return float((h[j, i] * (1 - ax) + h[j, i + 1] * ax) * (1 - ay) + (h[j + 1, i] * (1 - ax) + h[j + 1, i + 1] * ax) * ay)


def flora_counts(d: Path) -> Counter:
    """Natural refs a cell from the placer's shards (refs/flora/cy*.jsonl)."""
    n = Counter()
    for f in sorted(d.glob("cy*.jsonl")) if d.exists() else []:
        for line in f.read_text().splitlines():
            if line:
                o = json.loads(line)
                n[(math.floor(o["x"] / 4096), math.floor(o["y"] / 4096))] += 1
    return n


def density(refs, cells: dict) -> dict:
    """Mist refs a hectare by the cell's water kind (river and stream folded): refs [(cx, cy)], cells {"cx,cy": rec}."""
    mc = Counter(refs)
    area, got, top = Counter(), Counter(), Counter()
    for key, c in cells.items():
        w = c.get("water", "land").split("@")[0]      # a region's variant counts as its kind
        w = "river" if w.startswith("river") else "stream" if w.startswith("stream") else w
        xy = tuple(map(int, key.split(",")))
        area[w] += 1
        got[w] += mc.get(xy, 0)
        top[w] = max(top[w], mc.get(xy, 0))
    return {w: {"cells": area[w], "refs": got[w], "per_ha": round(got[w] / area[w] / CELL_HA, 2), "max_cell": top[w]} for w in area}


def spearman(a: list[float], b: list[float]) -> float:
    """Spearman's rank correlation (average ranks for ties)."""
    def ranks(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            for k in range(i, j + 1):
                r[order[k]] = (i + j) / 2
            i = j + 1
        return r
    ra, rb = ranks(a), ranks(b)
    ma, mb = sum(ra) / len(ra), sum(rb) / len(rb)
    cov = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    va, vb = sum((x - ma) ** 2 for x in ra), sum((y - mb) ** 2 for y in rb)
    return cov / math.sqrt(va * vb) if va and vb else 0.0




def rows(mist: list[dict], natural: list[dict], cells: dict) -> list[tuple[str, object, bool, str]]:
    """The verifier's mist rows over the refs read back from the ESM (dicts with cx, cy, edid, z, ground):
    (requirement, value, ok, detail)."""
    rc = atmosphere.region_classes()
    cls, _ = atmosphere.load_sources()
    xy = [(int(r["cx"]), int(r["cy"])) for r in mist]
    dens = density(xy, cells)
    out = []
    for k in ("blackwater-swamp", "green-marsh"):
        d = dens.get(k, {"per_ha": 0, "cells": 0})
        out.append((f"low mist over {k} water: refs a hectare at least {WATER_MIN} x Hjaalmarch's marsh ({HJAAL_PER_HA})",
                    d["per_ha"], d["per_ha"] >= WATER_MIN * HJAAL_PER_HA,
                    f"{d['cells']} cells; by water kind: " + ", ".join(f"{w} {v['per_ha']}" for w, v in sorted(dens.items()))))
    # graded by class: refs a hectare over each class's land and inland water cells, ranked against the class's density
    acc: dict[str, list[int]] = {}
    mc = Counter(xy)
    for key, c in cells.items():
        if c.get("water") != "sea" and c["region"] in rc:
            acc.setdefault(rc[c["region"]][0], []).append(mc.get(tuple(map(int, key.split(","))), 0))
    got = {cid: sum(v) / len(v) / CELL_HA for cid, v in acc.items() if v}
    order = sorted(got, key=lambda cid: cls["classes"][cid]["mist"]["density"])
    rank = spearman([cls["classes"][cid]["mist"]["density"] for cid in order], [got[cid] for cid in order])
    top2 = set(sorted(got, key=lambda cid: -got[cid])[:2])
    out.append(("low mist graded by atmosphere class: refs a hectare over each class's land and inland water follow the class's "
                "density (rank correlation at least 0.7, the water floors lifting water-rich coasts; the blackwater swamp and green marsh the two densest)",
                ", ".join(f"{cid} {got[cid]:.2f}" for cid in order), rank >= 0.7 and top2 == {"blackwater-swamp", "green-marsh"},
                f"rank correlation {rank:.2f}"))
    full = Counter((rc.get(cells.get(f"{r['cx']},{r['cy']}", {}).get("region"), (None,))[0], not r["edid"].endswith("HalfVis"))
                   for r in mist)
    share = {cid: full[(cid, True)] / max(1, full[(cid, True)] + full[(cid, False)]) for cid in ("blackwater-swamp", "green-marsh")}
    out.append(("stronger mist: the full-opacity share in the blackwater swamp and green marsh at least Hjaalmarch's 43 %",
                {k: round(v, 2) for k, v in share.items()}, all(v >= 0.43 for v in share.values()), ""))
    lift = sorted((float(r["z"]) - max(float(r["ground"]), 0.0)) / 70 for r in mist)
    q = (lift[len(lift) // 10], lift[len(lift) // 2], lift[9 * len(lift) // 10]) if lift else (0, 0, 0)
    out.append((f"below eye level: the centre over the water or ground p10/p50/p90 within {Z_M[0]} to {Z_M[1]} m, every ref within "
                f"{LIFT_RANGE[0]} to {LIFT_RANGE[1]} m", [round(v, 2) for v in (lift[0] if lift else 0, *q, lift[-1] if lift else 0)],
                bool(lift) and q[0] >= Z_M[0] - 0.05 and q[2] <= Z_M[1] + 0.05 and lift[0] >= LIFT_RANGE[0] and lift[-1] <= LIFT_RANGE[1],
                "min, p10, p50, p90, max; Hjaalmarch's p10/p50/p90 1.3/1.8/2.7 m"))
    nat = Counter((int(r["cx"]), int(r["cy"])) for r in natural)
    keys = set(mc) | set(nat)
    over = [k for k in keys if mc[k] + nat[k] > REFS_CAP]
    top = max(mc.values()) if mc else 0
    out.append((f"ref budget: mist at most {CAP} in a cell, natural plus mist at most {REFS_CAP}",
                f"mist max {top}, total max {max((mc[k] + nat[k] for k in keys), default=0)}", top <= CAP and not over,
                f"{len(over)} cells over"))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=REPO / "out/newworld/plugin")
    build(ap.parse_args(argv).out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
