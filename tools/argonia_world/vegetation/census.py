"""The trees-in-water census (lane 1.15-r6-trees-in-water): every placed stem of a tree role or a large shrub whose
ground stands under its cell's water level, or within WET_REACH_M of a LAND vertex under it (the water's footprint
grown by the freeboard), counted by region class and water type with the worst depths. Grass, aquatic plants,
mushrooms, deadwood and rocks are not stems. The lore's exception (place.in_water_ok): cypress and mangrove in the
marsh's blackwater only.

Skyrim.esm (0034, the audit in docs/research/2026-11-04/lane-1.15-r6-trees-in-water.md): its trees stand on dry
land; 5.8 % of Morthal's marsh trees have ground under their cell's water and none at the sea.

    python3 -m tools.argonia_world.vegetation census [--out out/terrain/vegetation] [--land out/terrain/land]
        prints the census as JSON; exit 1 when a stem outside the exception stands in water (each red names the
        cell, the form and the depth). The result is cached under <out>/census.json keyed by its stamp: the bytes
        of the shards and LAND rows it reads, the cell_water rows and the forms, and this module and place.py.
"""
from __future__ import annotations

import base64
import gzip
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

from tools.argonia_world import skyrim_units as su
from tools.argonia_world.terrain import quantize
from tools.argonia_world.vegetation import build, place

ROOT = Path(__file__).resolve().parents[3]
FIRST = 20  # reds listed


def _land(land: Path, cy: int) -> dict:
    out = {}
    p = land / build.shard_name(cy)
    if not p.exists():
        return out
    with gzip.open(p, "rt", encoding="ascii") as f:
        for line in f:
            c = json.loads(line)
            d = np.frombuffer(base64.b64decode(c["vhgt"]), dtype=np.int8).reshape(su.LAND_VERTS, su.LAND_VERTS)
            out[(c["x"], c["y"])] = quantize.decode(c["offset"], d) * su.VHGT_STEP_UNITS / su.UNITS_PER_METRE
    return out


def stamp(out: Path, land: Path, w) -> str:
    h = hashlib.sha256()
    for p in [Path(__file__), Path(place.__file__)] + sorted(out.glob("cy*.jsonl.gz")) + sorted(land.glob("cy*.jsonl.gz")):
        h.update(p.name.encode())
        h.update(p.read_bytes())
    for q in ("SELECT cx, cy, level_m, water_type FROM cell_water ORDER BY cx, cy",
              "SELECT * FROM object_form ORDER BY form_key",
              "SELECT route_id, flat_width_m FROM road ORDER BY route_id",
              "SELECT route_id, ord, x_m, y_m FROM road_point ORDER BY route_id, ord",
              "SELECT id, eco_class_id FROM land_region ORDER BY id"):
        h.update(repr([tuple(r) for r in w.query(q)]).encode())
    return h.hexdigest()


def cell_census(H, level, u, v):
    """Per stem of one cell: (wet, depth m). Depth is the level less the ground under the stem (both triangulations'
    mean); wet when the depth is over 0 or a LAND vertex within WET_REACH_M lies under the level."""
    za, zb, _gx, _gy, i, j = place.ground_at(H, u, v)
    depth = level - (za + zb) / 2
    wet = place.wet_near(H, level, u, v)
    return wet | (depth > 0), depth


ROAD_FIRST = 10  # the worst refs listed per road line
FLORA_SKIP = ("rock", "aquatic")  # not ground flora: a rock, a water plant (grass is GRAS on the LTEX, not placed here)


def road_lines(w):
    """[(route id, half width m, (n, 2, 2) segment ends in grid samples)] (routes/paint.py's lane width)."""
    from tools.argonia_world.routes import paint
    out = []
    for r in w.query("SELECT route_id, flat_width_m FROM road ORDER BY route_id"):
        pts = np.array([(p["y_m"], p["x_m"]) for p in w.query(
            "SELECT x_m, y_m FROM road_point WHERE route_id = ? ORDER BY ord", r["route_id"])], dtype=np.float64)
        if len(pts) >= 2:
            g = pts / su.PROVINCE_SAMPLE_M + paint.PAD
            out.append((r["route_id"], r["flat_width_m"] / 2, np.stack([g[:-1], g[1:]], axis=1)))
    return out


def grid_of(cx: int, cy: int, u, v):
    """Grid (row, col) samples of points in a cell (terrain/grid.py's rows and columns, the apron's pad)."""
    from tools.argonia_world.routes import paint
    q, s = su.QUADS_PER_CELL, su.VERTEX_SPACING_UNITS
    x0, y0 = su.PROVINCE_CELL_SW
    south = paint.PAD + su.PROVINCE_CELLS * q - (cy - y0) * q
    return south - np.asarray(v) / s, paint.PAD + (cx - x0) * q + np.asarray(u) / s


def road_census(cells, fm, roads, stems) -> dict:
    """(a) a stem whose body (its reach x scale, place.road_reach) overlaps a road's lane, (b) ground flora (any
    other placed form but a rock or a water plant) on the lane: counts and the worst refs by offset."""
    tol = 1.0 / su.PROVINCE_SAMPLE_M
    bb = [(rid, half, seg, seg.min(axis=1).min(0) - 0, seg.max(axis=1).max(0)) for rid, half, seg in roads]
    hits = {"stems_on_road": [], "flora_on_lane": []}
    for c in cells:
        cx, cy = c["x"], c["y"]
        ox, oy = su.cell_origin(cx, cy)
        refs = c["refs"]
        if not refs:
            continue
        a = np.asarray([r[2:] for r in refs], dtype=np.float64)
        pr, pc = grid_of(cx, cy, a[:, 0] - ox, a[:, 1] - oy)
        for rid, half, seg, lo, hi in bb:
            reach = half / su.PROVINCE_SAMPLE_M + place.ROAD_REACH_CAP_M / su.PROVINCE_SAMPLE_M + tol
            if pr.max() < lo[0] - reach or pr.min() > hi[0] + reach or pc.max() < lo[1] - reach or pc.min() > hi[1] + reach:
                continue
            d = place.seg_dist(pr, pc, seg) * su.PROVINCE_SAMPLE_M
            for k in np.nonzero(d < half + place.ROAD_REACH_CAP_M)[0]:
                f = fm[c["bases"][refs[k][1]]]
                stem = f["form_key"] in stems
                body = 0.0
                if f.get("bound_x1") is not None:
                    body = min(max(abs(f["bound_x0"]), abs(f["bound_x1"]), abs(f["bound_y0"]), abs(f["bound_y1"]))
                               / su.UNITS_PER_METRE * a[k, 6], place.ROAD_REACH_CAP_M)
                row = (round(float(d[k]), 2), f["edid"], f"{refs[k][0]:06X}", round(float(a[k, 0])),
                       round(float(a[k, 1])), rid, f"({cx},{cy})")
                if stem and d[k] < half + body:
                    hits["stems_on_road"].append(row)
                elif not stem and f["role_id"] not in FLORA_SKIP and d[k] < half:
                    hits["flora_on_lane"].append(row)
    out = {}
    for k, v in hits.items():
        v.sort()
        out[k] = {"count": len(v), "worst": [dict(zip(("offset_m", "form", "ref", "x", "y", "road", "cell"), r))
                                             for r in v[:ROAD_FIRST]]}
    return out


def run(out: Path, land: Path, w=None) -> dict:
    from tools.argonia_world import db
    w = w if w is not None else db.open()
    cw = {(r["cx"], r["cy"]): (r["level_m"], r["water_type"])
          for r in w.query("SELECT cx, cy, level_m, water_type FROM cell_water")}
    fm = {r["form_key"]: dict(r) for r in w.query(
        "SELECT form_key, role_id, edid, model, bound_x0, bound_x1, bound_y0, bound_y1, bound_z0, bound_z1 "
        "FROM object_form")}
    eco = {r["id"]: r["eco_class_id"] for r in w.query("SELECT id, eco_class_id FROM land_region")}
    stems = {k for k, f in fm.items() if place.is_stem(f)}
    counts: dict[str, dict] = defaultdict(lambda: {"stems": 0, "wet": 0, "excepted": 0, "worst_m": 0.0})
    reds: list[str] = []
    n_red = n_exc = n_stems = 0
    by_cy: dict[int, list] = defaultdict(list)
    for c in build.read_cells(out):
        by_cy[c["y"]].append(c)
    for cy in sorted(by_cy):
        H = _land(land, cy)
        for c in by_cy[cy]:
            cx = c["x"]
            idx = [k for k, r in enumerate(c["refs"]) if c["bases"][r[1]] in stems]
            if not idx or (cx, cy) not in H:
                continue
            lv, wt = cw.get((cx, cy), (None, "dry"))
            cls = eco.get(c["region"], "?")
            refs = np.asarray([c["refs"][k][2:5] for k in idx], dtype=np.float64)
            ox, oy = su.cell_origin(cx, cy)
            n_stems += len(idx)
            if lv is None:
                counts[f"{cls}/dry"]["stems"] += len(idx)
                continue
            wet, depth = cell_census(H[(cx, cy)], lv, refs[:, 0] - ox, refs[:, 1] - oy)
            row = counts[f"{cls}/{wt}"]
            row["stems"] += len(idx)
            for q in np.nonzero(wet)[0]:
                b = c["bases"][c["refs"][idx[q]][1]]
                if place.in_water_ok(fm[b], wt):
                    row["excepted"] += 1
                    n_exc += 1
                    continue
                row["wet"] += 1
                row["worst_m"] = round(max(row["worst_m"], float(depth[q])), 2)
                n_red += 1
                if len(reds) < FIRST:
                    reds.append(f"({cx},{cy}) {c['refs'][idx[q]][0]:06X} {fm[b]['edid']}: depth {depth[q]:+.2f} m "
                                f"({wt})")
    roads = road_census([c for v in by_cy.values() for c in v], fm, road_lines(w), stems)
    return {"roads": roads, "stems": n_stems, "in_water": n_red, "excepted": n_exc,
            "by_class_water": {k: dict(v) for k, v in sorted(counts.items())}, "red": reds}


def main(out: Path, land: Path) -> int:
    from tools.argonia_world import db
    if not any(out.glob("cy*.jsonl.gz")) or not land.is_dir():
        print(json.dumps({"skipped": f"no vegetation shards in {out} or no LAND in {land}"}))
        return 0
    w = db.open()
    st = stamp(out, land, w)
    cache = out / "census.json"
    res = None
    if cache.exists():
        try:
            old = json.loads(cache.read_text())
            res = old if old.get("stamp") == st else None
        except ValueError:
            res = None
    if res is None:
        res = {"stamp": st, **run(out, land, w)}
        cache.write_text(json.dumps(res, indent=1, sort_keys=True) + "\n")
    print(json.dumps(res, indent=1, sort_keys=True))
    for r in res["red"]:
        print(f"trees-census red: {r}", file=sys.stderr)
    for r in res["roads"]["stems_on_road"]["worst"]:
        print(f"trees-census red: a stem on the road: {r}", file=sys.stderr)
    return 1 if res["in_water"] or res["roads"]["stems_on_road"]["count"] else 0
