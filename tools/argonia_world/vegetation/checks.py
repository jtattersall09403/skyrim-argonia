"""The vegetation's L1 checks (2.W4 §a), over what the writer reads: the shards in <out>, against the LAND the
terrain wrote (<land>/cy*.jsonl.gz, decoded from its VHGT, not the placement's own ground), the water ArgoniaWorld.esm
places, the road and the built places.

    ground     every ref's z within GROUND_TOL_M of both triangulations of its LAND quad
    slope      the LAND quad's slope inside the form's band; the height inside its band
    water      dry-land flora never over water; every other form's depth (or minus its height above the local
               water table) inside its water posture
    road       no ref within a traced road's half width of its centreline, nor on a painted road or track sample
    places     no ref inside a built place's footprint (its refs' bounds plus the margin)
    budget     no cell over the cap; the counts per region and cell (max, p95)
    ids        every FormID in its cell's reserved slot, none twice
    lists      the object lists: no vanilla form or rock shape, every rock sunk by its OBND, a why, BM&V everywhere
    sha256     of the shards' bytes (two builds compare it: determinism)
"""
from __future__ import annotations

import base64
import gzip
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

from tools.argonia_world import skyrim_units as su
from tools.argonia_world.terrain import quantize
from tools.argonia_world.vegetation import build, forms, place
from tools.argonia_world.vegetation import lists as lists_mod

GROUND_TOL_M = 0.5
POSTURE_TOL_M = 0.15  # the check reads the LAND's quantised, patched heights where the placer read the float game ground:
# one ref of 734,650 sat 0.05 m past its posture band on that difference and failed round 4's build (2026-11-03 00:40)
SEAT_HOVER_U, SEAT_SINK_U = 10.0, 40.0  # a tree's trunk base over / under the ground (lane 1.15-r4-trees)
SLOPE_TOL_DEG = 0.01
FIRST = 5  # failures listed per check
TREE_BANDS, ECO_BAND = lists_mod.TREE_BANDS, lists_mod.ECO_BAND  # the band table lives in lists (the placer closes on it)
TREE_ROLES = lists_mod.BAND_TREE_ROLES
# a cell counts toward its tree band by lists.countable, the one definition the planner's targets use too
BAND_MIN_CELLS = lists_mod.BAND_MIN_CELLS
BAND_LO, BAND_HI, BAND_LO_FIELD = lists_mod.BAND_LO, lists_mod.BAND_HI, lists_mod.BAND_LO_FIELD
VANILLA_TREES_IN_WATER, VANILLA_TREE_WATER_P10_U = 0.058, 198.0


def land_heights(land: Path, cys: set[int]) -> dict[tuple[int, int], np.ndarray]:
    """{(x, y): (33, 33) metres [i from the south, j]} decoded from the LAND shards of the rows in `cys`."""
    out = {}
    for cy in sorted(cys):
        p = land / build.shard_name(cy)
        if not p.exists():
            continue
        with gzip.open(p, "rt", encoding="ascii") as f:
            for line in f:
                c = json.loads(line)
                d = np.frombuffer(base64.b64decode(c["vhgt"]), dtype=np.int8).reshape(su.LAND_VERTS, su.LAND_VERTS)
                out[(c["x"], c["y"])] = quantize.decode(c["offset"], d) * su.VHGT_STEP_UNITS / su.UNITS_PER_METRE
    return out


def run(out: Path, land: Path, water: Path, world=None, src=None, log=print, collect: dict | None = None) -> dict:
    from tools.argonia_world import db
    from tools.argonia_world.routes import paint as road_paint
    from tools.navmesh import inputs

    w = world if world is not None else db.open()
    src = src or inputs.ground_sources()
    rules = {(r, x.form_key): x for r, xs in build.load_rules(w).items() for x in xs}
    feet = build.footprints(w, src.pad)
    segs = build.road_segments(w)
    table = build.water_table(src, water)
    cw = build.cell_water(w)  # the placer's posture: one level per cell (water/solve.py) once cell_water has rows
    h = hashlib.sha256()
    for p in sorted(out.glob("cy*.jsonl.gz")):
        h.update(p.name.encode())
        h.update(p.read_bytes())
    fails: dict[str, list] = defaultdict(list)
    counts: dict[str, list[int]] = defaultdict(list)
    ids: set[int] = set()
    role = {r["form_key"]: r["role_id"] for r in w.query("SELECT form_key, role_id FROM object_form")}
    eco = {r["id"]: r["eco_class_id"] for r in w.query("SELECT id, eco_class_id FROM land_region")}
    trees: dict[str, list[int]] = defaultdict(list)  # trees per cell, by region
    tree_wet = [0, 0]  # trees below the waterline, trees
    tree_far: list[float] = []  # dry trees' distance (units) to the nearest wet vertex of their cell
    n = 0
    seats = {r["form_key"]: r["seat_units"] for r in w.query(
        "SELECT v.form_key, v.seat_units FROM vegetation_form v JOIN object_form f USING (form_key) "
        "WHERE f.role_id IN (" + ",".join(f"'{x}'" for x in lists_mod.SEATED_ROLES) + ")")}
    seat_stat = [0.0, 0.0, 0]  # the worst hover, the worst sink (units), trees checked
    placed: set[str] = set()  # base forms placed anywhere
    by_cy: dict[int, list[dict]] = defaultdict(list)
    for c in build.read_cells(out):
        by_cy[c["y"]].append(c)
    for cy in sorted(by_cy):
        H = land_heights(land, {cy})
        n_, s_ = src.cell_rows(cy)
        xs = [c["x"] for c in by_cy[cy]]
        w0, _ = src.cell_cols(min(xs))
        _, e0 = src.cell_cols(max(xs))
        x0u, ytop = su.cell_origin(min(xs), cy)[0], su.cell_origin(0, cy)[1] + su.CELL_UNITS
        LR = inputs.water_levels((min(xs), cy, max(xs), cy), n_, w0, (s_ - n_ + 1, e0 - w0 + 1), x0u, ytop,
                                 water).astype(np.float64) / su.UNITS_PER_METRE
        road = np.zeros(LR.shape, np.int16)
        road_paint.override_classes(road, n_, w0)
        PR = (road != 0) | np.isin(src.cover[n_ - src.pad:s_ - src.pad + 1, w0 - src.pad:e0 - src.pad + 1],
                                   build.ROAD_CLASSES)
        for c in by_cy[cy]:
            cx, region = c["x"], c["region"]
            refs = np.asarray([r[2:] for r in c["refs"]], dtype=np.float64)
            fids = [r[0] for r in c["refs"]]
            bases = [c["bases"][r[1]] for r in c["refs"]]
            placed.update(bases)
            n += len(fids)
            counts[region].append(len(fids))
            is_tree = np.asarray([role.get(b) in TREE_ROLES for b in bases], dtype=bool)
            if len(fids) > place.CAP:
                fails["budget"].append(f"({cx},{cy}): {len(fids)} refs over the cap {place.CAP}")
            for k, f in enumerate(fids):
                if f != place.ref_id(cx, cy, k) or f in ids:
                    fails["ids"].append(f"({cx},{cy}) ref {k}: {f:06X}")
                ids.add(f)
            if (cx, cy) not in H:
                fails["ground"].append(f"({cx},{cy}): no LAND in {land}")
                continue
            ox, oy = su.cell_origin(cx, cy)
            u, v = refs[:, 0] - ox, refs[:, 1] - oy
            z = refs[:, 2] / su.UNITS_PER_METRE
            if (u < 0).any() or (u >= su.CELL_UNITS).any() or (v < 0).any() or (v >= su.CELL_UNITS).any():
                fails["ids"].append(f"({cx},{cy}): a ref outside its cell")
            za, zb, gx, gy, i, j = place.ground_at(H[(cx, cy)], u, v)
            sunk = np.asarray([rules[(region, b)].sink_m if (region, b) in rules else 0.0 for b in bases]) * refs[:, 6]
            zg = z + sunk  # the ground under a sunk rock's pivot
            seated = np.asarray([b in seats for b in bases], dtype=bool)
            zg = np.where(seated, (za + zb) / 2, zg)  # a tree's base is held by the seat check below, its posture
            # read at the ground (place.py: the base sits within 10 u over / 40 u under either triangulation)
            off = np.maximum(np.abs(zg - za), np.abs(zg - zb))
            for k in np.nonzero(off > GROUND_TOL_M)[0][:FIRST]:
                fails["ground"].append(f"{fids[k]:06X} ({cx},{cy}): {off[k]:.2f} m off the LAND")
            # a tree's trunk base (its mod's own seat above the pivot, x scale) against the ground under it, both
            # triangulations: no base more than SEAT_HOVER_U above, none more than SEAT_SINK_U under (finding 4)
            seat_u = np.asarray([seats.get(b, np.nan) for b in bases]) * refs[:, 6]
            base_u = refs[:, 2] + seat_u
            for k in np.nonzero(np.isin(bases, list(seats)) | np.asarray(
                    [role.get(b) in lists_mod.SEATED_ROLES for b in bases], dtype=bool))[0]:
                if not np.isfinite(seat_u[k]):
                    fails["seat"].append(f"{fids[k]:06X} ({cx},{cy}) {bases[k]}: a tree with no measured seat")
                    continue
                hover = base_u[k] - min(za[k], zb[k]) * su.UNITS_PER_METRE
                sunk = max(za[k], zb[k]) * su.UNITS_PER_METRE - base_u[k]
                seat_stat[0] = max(seat_stat[0], hover)
                seat_stat[1] = max(seat_stat[1], sunk)
                seat_stat[2] += 1
                if hover > SEAT_HOVER_U + 0.5 or sunk > SEAT_SINK_U + 0.5:  # float rounding at the bound
                    fails["seat"].append(f"{fids[k]:06X} ({cx},{cy}) {bases[k]}: trunk base {hover:+.0f} u over / "
                                         f"{sunk:+.0f} u under the ground")
            sl = place.slope_deg(gx, gy)
            # this cell's water, road paint and table, over its vertices [i from the south, j]
            a, _ = src.cell_cols(cx)
            L = LR[:, a - w0:a - w0 + su.LAND_VERTS][::-1]
            painted = PR[:, a - w0:a - w0 + su.LAND_VERTS][::-1]
            rr = np.clip((np.arange(n_, s_ + 1) - src.pad) // place.TABLE_STEP, 0, table.shape[0] - 1)
            cc = np.clip((np.arange(a, a + 33) - src.pad) // place.TABLE_STEP, 0, table.shape[1] - 1)
            T = table[np.ix_(rr, cc)][::-1].astype(np.float64)
            if cw is not None:
                lv = cw.level(cx, cy)
                L = np.full(L.shape, -np.inf if lv is None else lv)
                T = np.full(T.shape, cw.nearest_level(cx, cy))
            # a tree band is Skyrim.esm's marsh cells with ground to stand on: a cell of open water (a lagoon's
            # sea floor) is no marsh cell, so it is left out of the mean (session 6)
            counted = lists_mod.countable(H[(cx, cy)], L)
            if counted:
                trees[region].append(int(is_tree.sum()))
            if collect is not None:  # the post-pass's view: this cell's trees and whether the band counts it
                collect[(cx, cy)] = (region, is_tree, counted)
            depth = place.depth_at(L, i, j, zg)
            pr, pc = s_ - v / su.VERTEX_SPACING_UNITS, a + u / su.VERTEX_SPACING_UNITS
            wet_v = np.argwhere(L > H[(cx, cy)])
            for k in np.nonzero(is_tree)[0]:
                tree_wet[0] += depth[k] > 0
                tree_wet[1] += 1
                if depth[k] <= 0 and len(wet_v):
                    d = np.hypot(wet_v[:, 0] - (v[k] / su.VERTEX_SPACING_UNITS), wet_v[:, 1] - (u[k] / su.VERTEX_SPACING_UNITS))
                    tree_far.append(float(d.min()) * su.VERTEX_SPACING_UNITS)
            on_paint = painted[i, j] | painted[i, j + 1] | painted[i + 1, j] | painted[i + 1, j + 1]
            road_d = [(half, place.seg_dist(pr, pc, seg)) for half, seg in build.roads_near(segs, n_, a, s_, a + 32)]
            for k, b in enumerate(bases):
                r = rules.get((region, b))
                if r is None:
                    fails["slope"].append(f"{fids[k]:06X}: {b} is not in {region}'s object list")
                    continue
                if not (r.min_slope - SLOPE_TOL_DEG <= sl[k] <= r.max_slope + SLOPE_TOL_DEG):
                    fails["slope"].append(f"{fids[k]:06X} ({cx},{cy}): {sl[k]:.1f} deg outside {r.min_slope}-{r.max_slope}")
                zk = (za[k] + zb[k]) / 2
                if (r.min_height is not None and zk < r.min_height - 0.01) or \
                        (r.max_height is not None and zk > r.max_height + 0.01):
                    fails["slope"].append(f"{fids[k]:06X} ({cx},{cy}): {zk:.1f} m outside its height band")
                t = T[i[k], j[k]]
                above = zk - (t if np.isfinite(t) else -np.inf)
                if not any(place.posture_ok(r, np.array([depth[k] + e]), np.array([above + e]))[0]
                           for e in (0.0, -POSTURE_TOL_M, POSTURE_TOL_M)):
                    what = "dry-land flora over water" if r.dry_only else "outside its water posture"
                    fails["water"].append(f"{fids[k]:06X} ({cx},{cy}) {b}: {what} (depth {depth[k]:.2f} m)")
                if on_paint[k] or any(d[k] < half for half, d in road_d):
                    fails["road"].append(f"{fids[k]:06X} ({cx},{cy}): on the road")
                for r0, c0, r1, c1 in feet:
                    if r0 <= pr[k] <= r1 and c0 <= pc[k] <= c1:
                        fails["places"].append(f"{fids[k]:06X} ({cx},{cy}): inside a built place's footprint")
    allc = [x for v in counts.values() for x in v]

    def stat(v):
        a = np.asarray(v or [0])
        return {"cells": len(v), "refs": int(a.sum()), "max": int(a.max()), "p95": round(float(np.percentile(a, 95)), 1)}
    res = {"refs": n, "sha256": h.hexdigest(), "province": stat(allc),
           "regions": {r: stat(v) for r, v in sorted(counts.items())}}
    fails["lists"] = lists(w)
    fails["climbable"], share = climbable(w, placed)
    res["climbable_share"] = share
    res["tree_counts"], fails["trees"] = tree_bands(trees, eco, tree_wet, tree_far)
    res["tree_seat"] = {"trees": seat_stat[2], "worst_hover_u": round(seat_stat[0], 1),
                        "worst_sink_u": round(seat_stat[1], 1)}
    for k in ("seat", "trees", "lists", "climbable", "ground", "slope", "water", "road", "places", "budget", "ids"):
        f = fails.get(k, [])
        res[k] = {"failures": len(f), **({"fail": f[:FIRST]} if f else {})}
    log(f"vegetation checks: {n} refs, sha256 {res['sha256'][:12]}")
    return res


def tree_bands(trees: dict[str, list[int]], eco: dict[str, str], wet: list[int], far: list[float]):
    """(report, failures): each region's trees per cell against its eco class's Skyrim.esm band, the share of trees
    in water and the p10 distance of dry trees to wet ground (reported, with vanilla's numbers)."""
    rep, errs = {}, []
    for r, v in sorted(trees.items()):
        band = ECO_BAND.get(eco.get(r, ""))
        a = np.asarray(v or [0], dtype=np.float64)
        row = {"band": band, "cells": len(v), "mean": round(float(a.mean()), 1), "p90": round(float(np.percentile(a, 90)), 1)}
        if band:
            m = TREE_BANDS[band][0]
            row["vanilla_mean"] = m
            lo = (BAND_LO_FIELD if band == "field" else BAND_LO) * m
            if len(v) >= BAND_MIN_CELLS and not (lo <= a.mean() <= BAND_HI * m):
                errs.append(f"{r} ({band}): {a.mean():.1f} trees per cell outside {lo:.1f}-{BAND_HI * m:.1f} "
                            f"(vanilla mean {m:g})")
        rep[r] = row
    out = {"regions": rep, "in_water_share": round(wet[0] / max(wet[1], 1), 4), "vanilla_in_water_share": VANILLA_TREES_IN_WATER,
           "dry_tree_p10_distance_u": round(float(np.percentile(far, 10)), 0) if far else None,
           "vanilla_p10_distance_u": VANILLA_TREE_WATER_P10_U}
    return out, errs


def readback(out: Path, esm: Path, gen: Path, env=None) -> dict:
    """The spliced plugin read back through Mutagen (ArgoniaGen `vegcheck`, binary overlay): every cell's
    Temporary group parses, and its vegetation REFRs per cell equal the shards'; the plugin's sha256 (two builds
    compare it)."""
    import subprocess
    lo = place.ref_id(*su.PROVINCE_CELL_SW, 0)
    hi = place.ref_id(su.PROVINCE_CELL_SW[0] + su.PROVINCE_CELLS - 1, su.PROVINCE_CELL_SW[1] + su.PROVINCE_CELLS - 1,
                      place.SLOT - 1)
    rb = out / "readback.jsonl"
    r = subprocess.run([str(gen), "vegcheck", "--in", str(esm), "--first", f"{lo:X}", "--last", f"{hi:X}",
                        "--out", str(rb)], capture_output=True, text=True, env=env, check=False)
    if r.returncode:
        return {"fail": [f"vegcheck failed: {(r.stdout + r.stderr)[-500:]}"]}
    got = {}
    for line in rb.read_text().splitlines():
        c = json.loads(line)
        got[(c["x"], c["y"])] = c["n"]
    want = {(c["x"], c["y"]): len(c["refs"]) for c in build.read_cells(out)}
    bad = [f"({x},{y}): {got.get((x, y), 0)} read back, {n} placed" for (x, y), n in sorted(want.items())
           if got.get((x, y), 0) != n] + [f"({x},{y}): {n} read back, none placed" for (x, y), n in sorted(got.items())
                                          if (x, y) not in want]
    res = {"cells": len(got), "refs": sum(got.values()), "sha256": hashlib.sha256(esm.read_bytes()).hexdigest()}
    if bad:
        res["fail"] = bad[:FIRST]
    return res


def climbable(w, placed: set[str]) -> tuple[list[str], dict]:
    """1.15 climbable collision (climb-anything.md section 1): every placed rock, cliff shell and tree form has a
    collision body Free Climb attaches to (forms.climbable: a rock Static or Terrain, a tree Static, Trees or Terrain,
    mass 0). A measured body that fails, or a rock never measured, is red; a tree form never measured (its NIF is in
    an archive not unpacked here) is counted as `unmeasured`, owed. The share per role is the report."""
    errs, share = [], {}
    for r in w.query("SELECT form_key, edid, role_id, collision_layer l, collision_mass m FROM object_form"):
        if r["form_key"] not in placed or r["role_id"] not in forms.CLIMBABLE_ROLES:
            continue
        s = share.setdefault(r["role_id"], {"forms": 0, "climbable": 0, "unmeasured": 0})
        s["forms"] += 1
        if r["l"] is None and r["role_id"] != "rock":
            s["unmeasured"] += 1
        elif forms.climbable(r["role_id"], r["l"], r["m"]):
            s["climbable"] += 1
        else:
            errs.append(f"{r['form_key']} {r['edid']} ({r['role_id']}): collision layer {r['l']} mass {r['m']}, "
                        "not climbable")
    return errs, share


def lists(w) -> list[str]:
    """The object lists' L1 (1.15 §e): no Skyrim.esm form, no form whose mesh no mod supplies, no rock with a
    vanilla shape; every rock sunk (sink_frac > 0, OBND known); every row with a why; BM&V forms in every list."""
    from tools.argonia_world.vegetation import lists as L
    errs = []
    for r in w.query("SELECT o.land_region_id, o.form_key, o.why, f.role_id, f.mesh_source, f.bound_z1, "
                     "f.bound_z0, v.sink_frac FROM land_region_object o JOIN object_form f USING (form_key) "
                     "LEFT JOIN vegetation_form v USING (form_key)"):
        where = f"{r['land_region_id']} {r['form_key']}"
        if r["form_key"].endswith(":Skyrim.esm") or r["mesh_source"] in (None, "vanilla"):
            errs.append(f"{where}: a vanilla form or mesh (retired)")
        if r["role_id"] == "rock" and (r["mesh_source"] in L.VANILLA_SHAPE or not r["sink_frac"]
                                       or r["bound_z1"] is None or r["bound_z1"] <= r["bound_z0"]):
            errs.append(f"{where}: a rock not sunk by its bounding box, or of a vanilla shape")
        if r["sink_frac"] is None:
            errs.append(f"{where}: no vegetation_form row")
        if not (r["why"] or "").strip():
            errs.append(f"{where}: no why")
    for r in w.query("SELECT l.id, (SELECT count(*) FROM land_region_object o JOIN object_form f USING (form_key) "
                     "WHERE o.land_region_id = l.id AND f.mod = 'bmv') n FROM land_region l WHERE border = 0"):
        if not r["n"]:
            errs.append(f"{r['id']}: no BM&V form in its object list")
    return errs
