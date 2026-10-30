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
from tools.argonia_world.vegetation import build, place

GROUND_TOL_M = 0.5
SLOPE_TOL_DEG = 0.01
FIRST = 5  # failures listed per check


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


def run(out: Path, land: Path, water: Path, world=None, src=None, log=print) -> dict:
    from tools.argonia_world import db
    from tools.argonia_world.routes import paint as road_paint
    from tools.navmesh import inputs

    w = world if world is not None else db.open()
    src = src or inputs.ground_sources()
    rules = {(r, x.form_key): x for r, xs in build.load_rules(w).items() for x in xs}
    feet = build.footprints(w, src.pad)
    segs = build.road_segments(w)
    table = build.water_table(src, water)
    h = hashlib.sha256()
    for p in sorted(out.glob("cy*.jsonl.gz")):
        h.update(p.name.encode())
        h.update(p.read_bytes())
    fails: dict[str, list] = defaultdict(list)
    counts: dict[str, list[int]] = defaultdict(list)
    ids: set[int] = set()
    n = 0
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
            n += len(fids)
            counts[region].append(len(fids))
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
            off = np.maximum(np.abs(z - za), np.abs(z - zb))
            for k in np.nonzero(off > GROUND_TOL_M)[0][:FIRST]:
                fails["ground"].append(f"{fids[k]:06X} ({cx},{cy}): {off[k]:.2f} m off the LAND")
            sl = place.slope_deg(gx, gy)
            # this cell's water, road paint and table, over its vertices [i from the south, j]
            a, _ = src.cell_cols(cx)
            L = LR[:, a - w0:a - w0 + su.LAND_VERTS][::-1]
            painted = PR[:, a - w0:a - w0 + su.LAND_VERTS][::-1]
            rr = np.clip((np.arange(n_, s_ + 1) - src.pad) // place.TABLE_STEP, 0, table.shape[0] - 1)
            cc = np.clip((np.arange(a, a + 33) - src.pad) // place.TABLE_STEP, 0, table.shape[1] - 1)
            T = table[np.ix_(rr, cc)][::-1].astype(np.float64)
            depth = place.depth_at(L, i, j, z)
            pr, pc = s_ - v / su.VERTEX_SPACING_UNITS, a + u / su.VERTEX_SPACING_UNITS
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
                if not place.posture_ok(r, np.array([depth[k]]), np.array([above]))[0]:
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
    for k in ("ground", "slope", "water", "road", "places", "budget", "ids"):
        f = fails.get(k, [])
        res[k] = {"failures": len(f), **({"fail": f[:FIRST]} if f else {})}
    log(f"vegetation checks: {n} refs, sha256 {res['sha256'][:12]}")
    return res


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
