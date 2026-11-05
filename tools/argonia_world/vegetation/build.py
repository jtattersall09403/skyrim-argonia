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
import hashlib
import json
import pickle
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

from tools.argonia_world import skyrim_units as su
from tools.argonia_world.vegetation import lists, place
from tools.argonia_world.vegetation.place import Rule

Q = su.QUADS_PER_CELL
BAND = 4  # cell rows per band
ROAD_CLASSES = (29, 30)  # TRACK, BC_ROAD (routes/paint.py)


def shard_name(cy: int) -> str:
    return f"cy{cy:+04d}.jsonl.gz"


# --- the rules -------------------------------------------------------------------------------------------------
def load_rules(w) -> dict[str, list[Rule]]:
    scale = {r["form_key"]: (r["scale_min"], r["scale_max"]) for r in w.query("SELECT * FROM vegetation_form")}
    sink = {r["form_key"]: Rule.sink_of(r["sink_frac"], r["bound_z0"], r["bound_z1"])
            + r["seat_units"] / su.UNITS_PER_METRE  # a tree's own mod's seat (lane 1.15-r4-trees, finding 4)
            for r in w.query("SELECT v.form_key, v.sink_frac, v.seat_units, f.bound_z0, f.bound_z1 "
                             "FROM vegetation_form v JOIN object_form f USING (form_key)")}
    upright = {r["form_key"]: lists.upright_share(r["sink_frac"]) for r in w.query("SELECT * FROM vegetation_form")}
    tree = {r["form_key"]: r["role_id"] in lists.BAND_TREE_ROLES for r in w.query("SELECT form_key, role_id FROM object_form")}
    reach = {r["form_key"]: min(max(abs(r["bound_x0"]), abs(r["bound_x1"]), abs(r["bound_y0"]), abs(r["bound_y1"]))
                                / su.UNITS_PER_METRE, place.ROAD_REACH_CAP_M)
             for r in w.query("SELECT form_key, bound_x0, bound_x1, bound_y0, bound_y1 FROM object_form "
                              "WHERE role_id <> 'rock' AND bound_x1 IS NOT NULL")}
    out: dict[str, list[Rule]] = defaultdict(list)
    for r in w.query("SELECT * FROM land_region_object ORDER BY land_region_id, form_key"):
        if r["form_key"] not in scale:
            raise KeyError(f"{r['form_key']}: no vegetation_form row (its scale range)")
        out[r["land_region_id"]].append(Rule(
            r["form_key"], r["density_per_ha"], r["clustering"], r["radius_m"], r["min_slope_deg"],
            r["max_slope_deg"], r["min_height_m"], r["max_height_m"], r["water_min_m"], r["water_max_m"],
            bool(r["conform"]), scale[r["form_key"]], sink[r["form_key"]], upright[r["form_key"]],
            tree.get(r["form_key"], False), reach.get(r["form_key"], 0.0)))
    return dict(out)


def cell_regions(w) -> dict[tuple[int, int], str]:
    out = {}
    for r in w.query("SELECT * FROM cell_region_run"):
        for cx in range(r["cx0"], r["cx1"] + 1):
            out[(cx, r["cy"])] = r["land_region_id"]
    return out


def keeps(w) -> dict[str, float]:
    return {r["land_region_id"]: r["keep"] for r in w.query("SELECT * FROM vegetation_region_budget")}


PROBE_PLACE = "place.studio.world-sample"  # tools/world_sample.py's probe markers


def footprints(w, pad: int) -> list[tuple[float, float, float, float]]:
    """Each built place's exterior footprint as a grid rectangle (row0, col0, row1, col1): its refs' bounds plus
    the margin."""
    m = place.PLACE_MARGIN_M
    out = []
    for r in w.query("SELECT c.place_id, min(r.x_m) x0, max(r.x_m) x1, min(r.y_m) y0, max(r.y_m) y1 FROM build_ref r "
                     "JOIN build_cell c ON c.id = r.cell_id WHERE c.kind = 'exterior' AND c.place_id <> ? GROUP BY c.place_id "
                     "ORDER BY c.place_id", PROBE_PLACE):  # the probe markers stand everywhere and clear nothing
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
    margin = (place.ROAD_MARGIN_M + place.ROAD_REACH_CAP_M) / su.PROVINCE_SAMPLE_M
    out = []
    for half, seg, bb in segs:
        reach = half + margin + 1
        k = (bb[:, 0] <= r1 + reach) & (bb[:, 2] >= r0 - reach) & (bb[:, 1] <= c1 + reach) & (bb[:, 3] >= c0 - reach)
        if k.any():
            out.append((half, seg[k]))
    return out


def cell_water(w):
    """water/solve.py's per-cell levels once the water lane has written cell_water; None before (the old field)."""
    if not w.values("SELECT count(*) FROM cell_water")[0]:
        return None
    from tools.argonia_world.water import solve
    return solve.load(w)


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
def _code_stamp() -> str:
    """The placement's code (this package), the band cache's code version."""
    h = hashlib.sha256()
    for f in sorted(Path(__file__).parent.glob("*.py")):
        h.update(f.name.encode() + f.read_bytes())
    return h.hexdigest()


def band_key(cis, rules, region) -> str:
    """A band's content stamp: the placement code and, per cell, its region's rules and every input place_cell reads
    (heights, levels, table, roads, footprints): equal keys place equal stems, so the band's cache is reused."""
    h = hashlib.sha256(_code_stamp().encode())
    for ci in cis:
        r = region[(ci.cx, ci.cy)]
        h.update(f"{ci.cx},{ci.cy},{r},{rules[r]!r}".encode())
        for k, v in sorted(vars(ci).items()):
            h.update(k.encode())
            _feed(h, v)
    return h.hexdigest()


def _feed(h, v) -> None:
    """Hash a value whole: arrays by their bytes (repr elides long ones), lists and tuples item by item."""
    if isinstance(v, np.ndarray):
        v = np.ascontiguousarray(v)
        h.update(f"a{v.shape}{v.dtype}".encode() + v.tobytes())
    elif isinstance(v, (list, tuple)):
        h.update(f"l{len(v)}(".encode())
        for x in v:
            _feed(h, x)
        h.update(b")")
    else:
        h.update(f"v{v!r};".encode())


def _band_path(out: Path, top: int) -> Path:
    return out / "_bands" / f"{top:+04d}.pkl"


def load_band(out: Path, top: int, key: str):
    try:
        k, got = pickle.loads(_band_path(out, top).read_bytes())
    except (OSError, EOFError, ValueError, pickle.UnpicklingError):
        return None
    return got if k == key else None


def save_band(out: Path, top: int, key: str, got) -> None:
    p = _band_path(out, top)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".part")
    tmp.write_bytes(pickle.dumps((key, got), protocol=pickle.HIGHEST_PROTOCOL))
    tmp.replace(p)


def province_cells(cells=None) -> list[tuple[int, int]]:
    x0, y0 = su.PROVINCE_CELL_SW
    allc = [(cx, cy) for cy in range(y0, y0 + su.PROVINCE_CELLS) for cx in range(x0, x0 + su.PROVINCE_CELLS)]
    if cells is None:
        return allc
    return [c for c in allc if any(a <= c[0] <= b and d <= c[1] <= e for a, d, b, e in cells)]


def run(out: Path, cells_path: Path, cells=None, budget: bool = False, world=None, src=None, log=print,
        ground: Path | None = None) -> dict:
    """Place every province cell's vegetation (or those in `cells`: boxes (x0, y0, x1, y1)); write the shards and
    summary.json. budget=True: compute each region's keep from these cells and write the budget rows (the whole
    province only)."""
    from tools.argonia_world import db
    from tools.argonia_world.routes import paint as road_paint
    from tools.argonia_world.terrain import build as tb
    from tools.navmesh import inputs

    t0 = time.time()
    w = world if world is not None else db.open()
    src = src or inputs.ground_sources(ground)
    rules = load_rules(w)
    region = cell_regions(w)
    keep = keeps(w)
    feet = footprints(w, src.pad)
    segs = road_segments(w)
    table = water_table(src, cells_path)
    cw = cell_water(w)
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
        cis = []
        for cy in band:
            n_, s_ = src.cell_rows(cy)
            for cx in rows_by_cy[cy]:
                a, _ = src.cell_cols(cx)
                win = (slice(n_ - r0, s_ - r0 + 1), slice(a - c0, a - c0 + Q + 1))
                Lc, Tc = L[win][::-1], T[win][::-1]
                if cw is not None:  # 1.15: one water level per cell (water/solve.py), the table its nearest level
                    lv = cw.level(cx, cy)
                    Lc = np.full(Lc.shape, -np.inf if lv is None else lv)
                    Tc = np.full(Tc.shape, cw.nearest_level(cx, cy))
                cis.append(place.CellInputs(cx, cy, H[win][::-1], Lc, Tc, painted[win][::-1],
                                            south_row=s_, west_col=a, roads=roads_near(segs, n_, a, s_, a + Q),
                                            footprints=near(feet, n_, a, s_, a + Q)))
        key = band_key(cis, rules, region)
        got = load_band(out, max(band), key)
        reused = got is not None
        if not reused:
            got = {}
            for ci in cis:
                p = place.place_cell(ci, rules[region[(ci.cx, ci.cy)]])
                p["tree"] = np.asarray([r.tree for r in rules[region[(ci.cx, ci.cy)]]], dtype=bool)[p["form"]]
                p["countable"] = lists.countable(ci.H, ci.L)  # the check's one definition of a standable cell
                got[(ci.cx, ci.cy)] = p
            save_band(out, max(band), key, got)
        else:
            stats["bands_reused"] = stats.get("bands_reused", 0) + 1
        placed.update(got)
        stats["cells"] += len(cis)
        log(f"vegetation: rows {max(band)}..{min(band)}{' reused' if reused else ''} ({time.time() - t0:.0f} s)")
    if budget:
        keep = _budget(w, placed, region)
    # the closed loop on the tree band: the stems are all held, so the region's tree keep is solved on them
    eco = {r["id"]: r["eco_class_id"] for r in w.query("SELECT id, eco_class_id FROM land_region")}
    tkeep, tinfo = tree_keeps(placed, region, keep, eco)
    for r, i in sorted(tinfo.items()):
        log(f"vegetation: trees {r}: {i['mean_before']} -> {i['mean_after']} a countable cell "
            f"(band {i['band'][0]:g}-{i['band'][1]:g}, tree keep {i['tree_keep']:.4f})"
            + (f"; SHORTFALL: candidate supply gives {i['supply_mean']} a cell" if i["shortfall"] else ""))
    for cy in cys:
        _write_row(out, cy, rows_by_cy[cy], placed, region, rules, keep, tkeep)
        for cx in rows_by_cy[cy]:
            placed[(cx, cy)] = _counts(placed[(cx, cy)], keep.get(region[(cx, cy)], 1.0), tkeep.get(region[(cx, cy)]))
    summary = _summary(placed, region, rules, keep, time.time() - t0)
    summary["tree_bands"] = tinfo
    (out / "summary.json").write_text(json.dumps(summary, indent=1, sort_keys=True) + "\n")
    return summary


def tree_keeps(placed, region, keep, eco) -> tuple[dict[str, float], dict[str, dict]]:
    """The tree band closed as a loop (the placer measures what the check will): per region with a band, the trees
    a countable cell (lists.countable, the check's one rule) holds after the budget; above the band's upper bound the
    region's trees are thinned to the band's mean (Skyrim.esm's), below its lower bound raised to the nearest of the
    mean and 1.25 x the bound, bounded by the candidate supply (a shortfall is reported). Trees keep when their
    draw (the position-seeded `thin`, so a window placed twice places identically) is under the region's tree keep;
    the keep is the draw that makes the mean land. Returns ({region: tree keep}, {region: report})."""
    by: dict[str, list] = defaultdict(list)
    for c, p in placed.items():
        by[region[c]].append(p)
    out, info = {}, {}
    for r, ps in sorted(by.items()):
        band = lists.ECO_BAND.get(eco.get(r, ""))
        cells = [p for p in ps if p["countable"]]
        if not band or len(cells) < lists.BAND_MIN_CELLS:
            continue
        lo, mean, hi = lists.band_limits(band)
        k = keep.get(r, 1.0)
        n = len(cells)
        now = sum(int(((p["thin"] < k) & p["tree"]).sum()) for p in cells) / n
        draws = np.sort(np.concatenate([p["thin"][p["tree"]] for p in cells] or [np.zeros(0)]))
        supply = draws.size / n
        row = {"band": [lo, hi], "cells": n, "mean_before": round(now, 1), "supply_mean": round(supply, 1),
               "shortfall": False}
        if now > hi:
            target = mean
        elif now < lo:
            target = min(mean, 1.25 * lo)
        else:
            row.update(tree_keep=k, mean_after=round(now, 1))
            info[r] = row
            continue
        want = int(round(target * n))
        if want >= draws.size:  # the whole supply
            tk = 1.0
            row["shortfall"] = supply < lo
        else:  # the draw that keeps `want` of the region's countable-cell trees
            tk = float(draws[want])
        out[r] = tk
        after = sum(int(((p["thin"] < tk) & p["tree"]).sum()) for p in cells) / n
        row.update(tree_keep=tk, mean_after=round(after, 1))
        info[r] = row
    return out, info


def _counts(p: dict, k: float, tk: float | None = None) -> dict:
    """What the summary keeps of a cell once written: the stems before and after the budget, per form."""
    m = place.final_mask(p["thin"], p["tree"], k, tk)
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


def _write_row(out: Path, cy: int, cxs: list[int], placed, region, rules, keep, tkeep) -> None:
    lines = []
    for cx in sorted(cxs):
        p = placed[(cx, cy)]
        rl = rules[region[(cx, cy)]]
        m = place.final_mask(p["thin"], p["tree"], keep.get(region[(cx, cy)], 1.0), tkeep.get(region[(cx, cy)]))
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


def tree_score(refs: np.ndarray) -> np.ndarray:
    """A keep score in [0, 1) per ref from its position alone (x, y in units, 2 dp), so the same stem scores the
    same in any window and any run."""
    k = np.round(refs[:, :2] * 100).astype(np.int64).astype(np.uint64)
    h = k[:, 0] * np.uint64(0x9E3779B97F4A7C15) ^ (k[:, 1] * np.uint64(0xC2B2AE3D27D4EB4F))
    h ^= h >> np.uint64(29)
    h *= np.uint64(0xBF58476D1CE4E5B9)
    h ^= h >> np.uint64(32)
    return (h >> np.uint64(11)).astype(np.float64) / float(1 << 53)


def close_tree_bands(out: Path, land: Path, water: Path, world=None, src=None, log=print, rounds: int = 3) -> dict:
    """After all placement, the check's own tree count decides: for a region the check (checks.run, on these shards
    and this LAND) reports above its band, thin its trees (all cells) with the position-seeded score until the
    check's count reports the band's mean; repeat up to `rounds` times. A region under its band is a shortfall
    (supply), reported, never thinned or red. Returns {region: {"before", "after", "rounds"}}."""
    from tools.argonia_world import db
    from tools.argonia_world.vegetation import checks
    w = world if world is not None else db.open()
    eco = {r["id"]: r["eco_class_id"] for r in w.query("SELECT id, eco_class_id FROM land_region")}
    report: dict[str, dict] = {}
    for rd in range(rounds + 1):
        col: dict = {}
        checks.run(out, land, water, world=w, src=src, log=lambda *_: None, collect=col)
        cells = defaultdict(list)
        for (cx, cy), (r, tr, counted) in col.items():
            if counted:
                cells[r].append(int(tr.sum()))
        thin = {}
        for r, v in sorted(cells.items()):
            band = lists.ECO_BAND.get(eco.get(r, ""))
            if not band or len(v) < lists.BAND_MIN_CELLS:
                continue
            lo, mean, hi = lists.band_limits(band)
            m = sum(v) / len(v)
            report.setdefault(r, {"before": round(m, 1)})
            if m > hi * 0.999 and rd < rounds:
                thin[r] = (len(v), mean)
            else:
                report[r].update(after=round(m, 1), rounds=rd, shortfall=m < lo)
        if not thin:
            break
        scores: dict[str, list] = defaultdict(list)
        shards = {}
        for cy in sorted({cy for _, cy in col}):
            p = out / shard_name(cy)
            if p.exists():
                with gzip.open(p, "rt", encoding="ascii") as f:
                    shards[cy] = [json.loads(line) for line in f]
        trees_of = {}
        for cy, cs in shards.items():
            for c in cs:
                key = (c["x"], cy)
                if c["region"] in thin and key in col:
                    refs = np.asarray([x[2:4] for x in c["refs"]], dtype=np.float64).reshape(-1, 2)
                    sc = tree_score(refs)
                    trees_of[key] = (sc, col[key][1])
                    if col[key][2]:
                        scores[c["region"]].extend(sc[col[key][1]].tolist())
        tk = {}
        for r, (n, mean) in thin.items():
            d = np.sort(np.asarray(scores[r]))
            want = int(round(mean * n))
            tk[r] = float(d[want]) if want < d.size else 2.0
        for cy, cs in shards.items():
            changed, lines = False, []
            for c in cs:
                key = (c["x"], cy)
                if key in trees_of:
                    sc, tr = trees_of[key]
                    keepm = ~(tr & (sc >= tk[c["region"]]))
                    if not keepm.all():
                        changed = True
                        c["refs"] = [x for x, k in zip(c["refs"], keepm) if k]
                        for k, x in enumerate(c["refs"]):
                            x[0] = place.ref_id(c["x"], cy, k)
                if c["refs"]:
                    lines.append(json.dumps(c, separators=(",", ":"), sort_keys=True))
            if changed:
                with open(out / shard_name(cy), "wb") as f, gzip.GzipFile(fileobj=f, mode="wb", mtime=0, filename="") as z:
                    z.write(("\n".join(lines) + "\n").encode("ascii"))
    for r, i in sorted(report.items()):
        if "after" in i and i["after"] != i["before"]:
            log(f"vegetation: trees {r}: {i['before']} -> {i['after']} by the check's count, {i['rounds']} round(s)")
        if i.get("shortfall"):
            log(f"vegetation: trees {r}: SHORTFALL (supply) {i['after']} a cell")
    return report
