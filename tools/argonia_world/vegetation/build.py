"""The province's vegetation, one band of cell rows at a time (place.py's rules over the game's ground and water).

Output under <out> (ArgoniaGen's VegetationRecords.cs reads it into ArgoniaWorld.esm, decision 0031 §1):
    cy<+NNN>.jsonl.gz   one line per province cell with stems, x ascending:
                        {"x", "y", "region", "bases": [FormKey], "refs": [[local FormID, base index, x, y, z (units),
                         rx, ry, rz (radians), scale]]}
                        (gzip with no timestamp, so the bytes are stable)
    summary.json        counts per region and cell, the budget, the inputs, time
Nothing whole-province is held but the water-table map (505 x 505) and, with `budget=True`, each cell's stems until
the region keeps are known.
"""
from __future__ import annotations

import gzip
import json
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

from tools.argonia_world import skyrim_units as su
from tools.argonia_world.vegetation import place
from tools.argonia_world.vegetation.place import Rule

Q = su.QUADS_PER_CELL
BAND = 4  # cell rows per band
ROAD_CLASSES = (29, 30)  # TRACK, BC_ROAD (routes/paint.py)


def shard_name(cy: int) -> str:
    return f"cy{cy:+04d}.jsonl.gz"


# --- the rules -------------------------------------------------------------------------------------------------
def load_rules(w) -> dict[str, list[Rule]]:
    scale = {r["form_key"]: (r["scale_min"], r["scale_max"]) for r in w.query("SELECT * FROM vegetation_form")}
    out: dict[str, list[Rule]] = defaultdict(list)
    for r in w.query("SELECT * FROM land_region_object ORDER BY land_region_id, form_key"):
        if r["form_key"] not in scale:
            raise KeyError(f"{r['form_key']}: no vegetation_form row (its scale range)")
        out[r["land_region_id"]].append(Rule(
            r["form_key"], r["density_per_ha"], r["clustering"], r["radius_m"], r["min_slope_deg"],
            r["max_slope_deg"], r["min_height_m"], r["max_height_m"], r["water_min_m"], r["water_max_m"],
            bool(r["conform"]), scale[r["form_key"]]))
    return dict(out)


def cell_regions(w) -> dict[tuple[int, int], str]:
    out = {}
    for r in w.query("SELECT * FROM cell_region_run"):
        for cx in range(r["cx0"], r["cx1"] + 1):
            out[(cx, r["cy"])] = r["land_region_id"]
    return out


def keeps(w) -> dict[str, float]:
    return {r["land_region_id"]: r["keep"] for r in w.query("SELECT * FROM vegetation_region_budget")}


def footprints(w, pad: int) -> list[tuple[float, float, float, float]]:
    """Each built place's exterior footprint as a grid rectangle (row0, col0, row1, col1): its refs' bounds plus
    the margin."""
    m = place.PLACE_MARGIN_M
    out = []
    for r in w.query("SELECT c.place_id, min(r.x_m) x0, max(r.x_m) x1, min(r.y_m) y0, max(r.y_m) y1 FROM build_ref r "
                     "JOIN build_cell c ON c.id = r.cell_id WHERE c.kind = 'exterior' GROUP BY c.place_id "
                     "ORDER BY c.place_id"):
        s = su.PROVINCE_SAMPLE_M
        out.append(((r["y0"] - m) / s + pad, (r["x0"] - m) / s + pad, (r["y1"] + m) / s + pad, (r["x1"] + m) / s + pad))
    return out


def near(rects, r0, c0, r1, c1, reach: float = 0.0):
    return [t for t in rects if t[0] <= r1 + reach and t[2] >= r0 - reach and t[1] <= c1 + reach and t[3] >= c0 - reach]


def road_segments(world) -> list[tuple[float, np.ndarray, np.ndarray]]:
    """[(half width in samples, segments (n, 2, 2), their bounds (n, 4) r0 c0 r1 c1)] (routes/paint.py's)."""
    from tools.argonia_world.routes import paint as road_paint
    out = []
    for _, half, seg in road_paint.segments(world):
        lo, hi = seg.min(axis=1), seg.max(axis=1)
        out.append((half, seg, np.concatenate([lo, hi], axis=1)))
    return out


def roads_near(segs, r0, c0, r1, c1):
    margin = place.ROAD_MARGIN_M / su.PROVINCE_SAMPLE_M
    out = []
    for half, seg, bb in segs:
        reach = half + margin + 1
        k = (bb[:, 0] <= r1 + reach) & (bb[:, 2] >= r0 - reach) & (bb[:, 1] <= c1 + reach) & (bb[:, 3] >= c0 - reach)
        if k.any():
            out.append((half, seg[k]))
    return out


# --- the water table -------------------------------------------------------------------------------------------
def water_table(src, cells_path: Path) -> np.ndarray:
    """The local water table over the province on a coarse map (TABLE_STEP samples a tile, metres): a tile with
    water over any of its samples has its highest such level; every other tile the level of the nearest wet tile
    (grown ring by ring; where two meet, the higher). NaN only when the province has no water."""
    from tools.navmesh import inputs

    n, p, t = src.n + 1, src.pad, place.TABLE_STEP
    x0u = su.cell_origin(*su.PROVINCE_CELL_SW)[0]
    ytop = su.cell_origin(su.PROVINCE_CELL_SW[0], su.PROVINCE_CELL_SW[1] + su.PROVINCE_CELLS)[1]
    box = (su.PROVINCE_CELL_SW[0], su.PROVINCE_CELL_SW[1], su.PROVINCE_CELL_SW[0] + su.PROVINCE_CELLS - 1,
           su.PROVINCE_CELL_SW[1] + su.PROVINCE_CELLS - 1)
    level = inputs.water_levels(box, p, p, (n, n), x0u, ytop, cells_path) / np.float32(su.UNITS_PER_METRE)
    k = -(-n // t)
    tl = np.full((k, k), -np.inf, np.float32)
    for a in range(0, n, 256):  # row bands of the raw ground (the coarse map needs no quantisation)
        b = min(a + 256, n)
        g = np.asarray(src.ground[a:b], dtype=np.float32)
        lv = np.where(level[a:b] > g, level[a:b], -np.inf).astype(np.float32)
        rows = -(-(b - a) // t)
        padded = np.full((rows * t, k * t), -np.inf, np.float32)
        padded[:b - a, :n] = lv
        tl[a // t:a // t + rows] = np.maximum(tl[a // t:a // t + rows],
                                              padded.reshape(rows, t, k, t).max(axis=(1, 3)))
    del level
    have = np.isfinite(tl)
    if not have.any():
        return np.full((k, k), np.nan, np.float32)
    cur = np.where(have, tl, -np.inf)
    while not have.all():
        grown = cur.copy()
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr or dc:
                    sh = np.full_like(cur, -np.inf)
                    sh[max(dr, 0):k + min(dr, 0), max(dc, 0):k + min(dc, 0)] = \
                        cur[max(-dr, 0):k + min(-dr, 0), max(-dc, 0):k + min(-dc, 0)]
                    grown = np.maximum(grown, sh)
        new = ~have & np.isfinite(grown)
        cur = np.where(have, cur, grown)
        have = have | new
    return cur


# --- the province ----------------------------------------------------------------------------------------------
def province_cells(cells=None) -> list[tuple[int, int]]:
    x0, y0 = su.PROVINCE_CELL_SW
    allc = [(cx, cy) for cy in range(y0, y0 + su.PROVINCE_CELLS) for cx in range(x0, x0 + su.PROVINCE_CELLS)]
    if cells is None:
        return allc
    return [c for c in allc if any(a <= c[0] <= b and d <= c[1] <= e for a, d, b, e in cells)]


def run(out: Path, cells_path: Path, cells=None, budget: bool = False, world=None, src=None, log=print) -> dict:
    """Place every province cell's vegetation (or those in `cells`: boxes (x0, y0, x1, y1)); write the shards and
    summary.json. budget=True: compute each region's keep from these cells and write the budget rows (the whole
    province only)."""
    from tools.argonia_world import db
    from tools.argonia_world.routes import paint as road_paint
    from tools.argonia_world.terrain import build as tb
    from tools.navmesh import inputs

    t0 = time.time()
    w = world if world is not None else db.open()
    src = src or inputs.ground_sources()
    rules = load_rules(w)
    region = cell_regions(w)
    keep = keeps(w)
    feet = footprints(w, src.pad)
    segs = road_segments(w)
    table = water_table(src, cells_path)
    log(f"vegetation: rules for {len(rules)} regions, water table {table.shape} ({time.time() - t0:.0f} s)")
    todo = [c for c in province_cells(cells) if region.get(c) in rules]
    rows_by_cy: dict[int, list[int]] = defaultdict(list)
    for cx, cy in todo:
        rows_by_cy[cy].append(cx)
    placed: dict[tuple[int, int], dict] = {}
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("cy*.jsonl.gz"):
        old.unlink()
    cys = sorted(rows_by_cy, reverse=True)
    stats = {"cells": 0, "candidates_accepted": 0}
    for bi in range(0, len(cys), BAND):
        band = cys[bi:bi + BAND]
        north, _ = src.cell_rows(max(band))
        _, south = src.cell_rows(min(band))
        cxs = sorted({cx for cy in band for cx in rows_by_cy[cy]})
        west, _ = src.cell_cols(cxs[0])
        _, east = src.cell_cols(cxs[-1])
        r0, r1, c0, c1 = north, south + 1, west, east + 1
        shape = (r1 - r0, c1 - c0)
        H = tb.game_heights_m(src, r0, r1, c0, c1)
        x0u = su.cell_origin(cxs[0], 0)[0]
        ytop = su.cell_origin(0, max(band))[1] + su.CELL_UNITS
        box = (cxs[0], min(band), cxs[-1], max(band))
        L = inputs.water_levels(box, r0, c0, shape, x0u, ytop, cells_path).astype(np.float64) / su.UNITS_PER_METRE
        road = np.zeros(shape, np.int16)
        road_paint.override_classes(road, r0, c0)
        painted = (road != 0) | np.isin(src.classes(r0, r1, c0, c1, H), ROAD_CLASSES)
        rr = np.clip((np.arange(r0, r1) - src.pad) // place.TABLE_STEP, 0, table.shape[0] - 1)
        cc = np.clip((np.arange(c0, c1) - src.pad) // place.TABLE_STEP, 0, table.shape[1] - 1)
        T = table[np.ix_(rr, cc)].astype(np.float64)
        for cy in band:
            n_, s_ = src.cell_rows(cy)
            for cx in rows_by_cy[cy]:
                a, _ = src.cell_cols(cx)
                win = (slice(n_ - r0, s_ - r0 + 1), slice(a - c0, a - c0 + Q + 1))
                ci = place.CellInputs(cx, cy, H[win][::-1], L[win][::-1], T[win][::-1], painted[win][::-1],
                                      south_row=s_, west_col=a, roads=roads_near(segs, n_, a, s_, a + Q),
                                      footprints=near(feet, n_, a, s_, a + Q))
                placed[(cx, cy)] = place.place_cell(ci, rules[region[(cx, cy)]])
                stats["cells"] += 1
        if not budget:  # write as we go: nothing held across bands
            for cy in band:
                _write_row(out, cy, rows_by_cy[cy], placed, region, rules, keep)
                for cx in rows_by_cy[cy]:
                    placed[(cx, cy)] = _counts(placed[(cx, cy)], keep.get(region[(cx, cy)], 1.0))
        log(f"vegetation: rows {max(band)}..{min(band)} ({time.time() - t0:.0f} s)")
    if budget:
        keep = _budget(w, placed, region)
        for cy in cys:
            _write_row(out, cy, rows_by_cy[cy], placed, region, rules, keep)
            for cx in rows_by_cy[cy]:
                placed[(cx, cy)] = _counts(placed[(cx, cy)], keep.get(region[(cx, cy)], 1.0))
    summary = _summary(placed, region, rules, keep, time.time() - t0)
    (out / "summary.json").write_text(json.dumps(summary, indent=1, sort_keys=True) + "\n")
    return summary


def _counts(p: dict, k: float) -> dict:
    """What the summary keeps of a cell once written: the stems before and after the budget, per form."""
    m = p["thin"] < k
    return {"before": int(p["thin"].size), "after": int(m.sum()), "forms": np.bincount(p["form"][m]).tolist()}


def _budget(w, placed, region) -> dict[str, float]:
    worst: dict[str, float] = {}
    densest: dict[str, int] = {}
    counts: dict[str, list[int]] = defaultdict(list)
    for c, p in placed.items():
        r = region[c]
        worst[r] = min(worst.get(r, 1.0), place.threshold(p["thin"]))
        densest[r] = max(densest.get(r, 0), int(p["thin"].size))
        counts[r].append(int(p["thin"].size))
    out = {}
    for r in sorted(worst):
        v = place.vanilla_keep(counts[r])
        t = min(worst[r], v)
        k = 1.0 if t >= 1.0 else place.keep_value(t)
        out[r] = k
        a = np.asarray(counts[r])
        w.upsert("vegetation_region_budget", land_region_id=r, keep=k, cap=place.CAP, densest_cell_refs=densest[r],
                 why=(f"2.W4 veg: before the budget p95 {np.percentile(a, 95):.0f} and max {densest[r]} stems a cell; "
                      f"keep {k} brings them to vanilla's forested cells (p95 {place.VANILLA_P95}, max "
                      f"{place.VANILLA_MAX}) and holds every cell at or under the cap {place.CAP} (owed its L4 measurement)"))
    w.save(["vegetation_region_budget"])
    return out


def _write_row(out: Path, cy: int, cxs: list[int], placed, region, rules, keep) -> None:
    lines = []
    for cx in sorted(cxs):
        p = placed[(cx, cy)]
        rl = rules[region[(cx, cy)]]
        m = p["thin"] < keep.get(region[(cx, cy)], 1.0)
        idx = np.nonzero(m)[0]
        if not idx.size:
            continue
        if idx.size > place.SLOT:
            raise ValueError(f"cell ({cx},{cy}): {idx.size} stems over its FormID slot of {place.SLOT}")
        used = sorted({int(f) for f in p["form"][idx]})
        bidx = {f: k for k, f in enumerate(used)}
        ox, oy = su.cell_origin(cx, cy)
        refs = []
        for k, q in enumerate(idx.tolist()):
            refs.append([place.ref_id(cx, cy, k), bidx[int(p["form"][q])],
                         su.rounded(ox + p["u"][q], 2), su.rounded(oy + p["v"][q], 2),
                         su.rounded(su.metres_to_units(p["z"][q]), 2),
                         su.rounded(p["rx"][q], 6), su.rounded(p["ry"][q], 6), su.rounded(p["rz"][q], 6),
                         su.rounded(p["scale"][q], 4)])
        lines.append(json.dumps({"x": cx, "y": cy, "region": region[(cx, cy)],
                                 "bases": [rl[f].form_key for f in used], "refs": refs},
                                separators=(",", ":"), sort_keys=True))
    if lines:
        with open(out / shard_name(cy), "wb") as f, gzip.GzipFile(fileobj=f, mode="wb", mtime=0, filename="") as z:
            z.write(("\n".join(lines) + "\n").encode("ascii"))


def _summary(placed, region, rules, keep, seconds: float) -> dict:
    by_region: dict[str, list[int]] = defaultdict(list)
    before: dict[str, int] = defaultdict(int)
    forms: dict[str, int] = defaultdict(int)
    for c, p in placed.items():
        r = region[c]
        by_region[r].append(p["after"])
        before[r] += p["before"]
        for f, n in enumerate(p["forms"]):
            if n:
                forms[rules[r][f].form_key] += n
    allc = [n for v in by_region.values() for n in v]
    densest = sorted(placed, key=lambda c: (-placed[c]["after"], c))[:10]

    def stat(v):
        a = np.asarray(v) if v else np.zeros(1)
        return {"cells": len(v), "refs": int(a.sum()), "max": int(a.max()), "p95": float(np.percentile(a, 95)),
                "mean": round(float(a.mean()), 1)}
    return {"cap": place.CAP, "seconds": round(seconds, 1), "province": stat(allc),
            "regions": {r: {**stat(v), "before": before[r], "keep": keep.get(r, 1.0)} for r, v in sorted(by_region.items())},
            "forms": dict(sorted(forms.items())), "densest": [[c[0], c[1], placed[c]["after"]] for c in densest]}


def read_cells(out: Path):
    for p in sorted(out.glob("cy*.jsonl.gz")):
        with gzip.open(p, "rt", encoding="ascii") as f:
            for line in f:
                yield json.loads(line)
