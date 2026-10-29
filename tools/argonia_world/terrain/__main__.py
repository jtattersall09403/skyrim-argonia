"""The terrain generator's command line (2.W1).

    python3 -m tools.argonia_world.terrain build [--cells=x0,y0,x1,y1] [--out DIR] [--no-apron]   (the = keeps a leading minus an argument)
        every cell's LAND line into DIR/land/ (default out/terrain/), the build stats into DIR/stats.json
    python3 -m tools.argonia_world.terrain build --sample [--out DIR]   the gate's fixed sample (world.SAMPLE)
    python3 -m tools.argonia_world.terrain world [--out DIR]   DIR/world.json, the WRLD intermediate over DIR/land
    python3 -m tools.argonia_world.terrain check [--out DIR] [--points N]
        the L1 checks on what `build` wrote: inputs by sha256, height error at N random province vertices and
        over every province vertex (limiter-moved vertices counted apart), seams (heights and normals across every
        shared cell edge), layers per quadrant, and the overflow survey; DIR/check.json, and the sampled points
        with their expected heights in DIR/probe-points.json (the L4 terrain-heights scene); exit 1 on a failure

Memory: the arrays are memory-mapped and both commands stream one row of cells at a time.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

from tools.argonia_world import skyrim_units as su
from tools.argonia_world.terrain import build as B
from tools.argonia_world.terrain import quantize, vault, world
from tools.argonia_world.terrain.grid import Sources
from tools.argonia_world.terrain.landcover import table

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "out" / "terrain"
HEIGHT_TOL_M = 0.5  # the brief's L1/L4 bound
QUANT_M = 0.5 * su.VHGT_STEP_UNITS / su.UNITS_PER_METRE + 1e-6  # rounding to a step alone stays within this


def _cells(s: str | None):
    if not s:
        return None
    v = tuple(int(t) for t in s.split(","))
    if len(v) != 4:
        raise SystemExit("--cells takes x0,y0,x1,y1")
    return v


def cmd_build(a) -> int:
    src = Sources.load(apron=not a.no_apron)
    out = Path(a.out)

    def progress(cy, st):
        if cy % 16 == 0:
            print(f"  row {cy:+d}: {st.cells} cells", flush=True)

    from tools.argonia_world import db
    st = B.build(src, table(db.open()), out, cells=world.SAMPLE if a.sample else _cells(a.cells), progress=progress)
    d = {k: (v if not isinstance(v, dict) else {str(i): n for i, n in sorted(v.items())}) for k, v in st.__dict__.items()}
    d["cells_arg"] = "sample" if a.sample else a.cells
    d["apron"] = not a.no_apron
    (out / "stats.json").write_text(json.dumps(d, indent=1, sort_keys=True) + "\n")
    print(json.dumps(d, sort_keys=True))
    return 0


def _decode_m(c: dict) -> np.ndarray:
    return quantize.decode(c["offset"], B.unpack(c)["vhgt"]) * su.VHGT_STEP_UNITS / su.UNITS_PER_METRE


def cmd_check(a) -> int:
    out = Path(a.out)
    stats = json.loads((out / "stats.json").read_text())
    src = Sources.load(apron=stats.get("apron", True))
    res: dict = {"inputs": {n: s for n, s in vault.status(vault.data_dir()).items()
                            if n in ("refined-height-f32.npy", "landcover-i16.npy", "apron-source-near.npy", "ground-tint.png")}}
    fails = [f"input {n}: {s}" for n, s in res["inputs"].items() if s != "ok"]

    # random province vertices among the built cells (seeded: the same points every run)
    built = sorted(int(p.name[2:6]) for p in (out / "land").glob("cy*.jsonl.gz"))
    rng = np.random.default_rng(20261029)
    pts: dict[tuple[int, int], list[tuple[int, int]]] = {}
    span = src.n // su.QUADS_PER_CELL
    x0, y0 = su.PROVINCE_CELL_SW
    for _ in range(a.points):
        cx, cy = int(rng.integers(x0, x0 + span)), int(rng.integers(y0, y0 + span))
        pts.setdefault((cx, cy), []).append((int(rng.integers(0, su.LAND_VERTS)), int(rng.integers(0, su.LAND_VERTS))))

    seam_h = seam_n = edges = 0
    sampled, sample_errs, sample_lim, probes = 0, [], [], []
    all_max = all_max_nolim = 0.0
    limited_v = 0
    max_layers = 0
    prev: dict[int, tuple[np.ndarray, np.ndarray]] = {}  # x -> the north row's south edge (heights, normals)
    for cy in sorted(built, reverse=True):  # north to south, the order build wrote
        row = {}
        with __import__("gzip").open(out / "land" / B.shard_name(cy), "rt", encoding="ascii") as f:
            for line in f:
                c = json.loads(line)
                h = quantize.decode(c["offset"], B.unpack(c)["vhgt"])
                n = B.unpack(c)["vnml"]
                row[c["x"]] = (h, n)
                max_layers = max([max_layers] + [len(q["layers"]) for q in c["quads"]])
                if src.in_province(c["x"], cy):
                    hm = h * su.VHGT_STEP_UNITS / su.UNITS_PER_METRE
                    north, south = src.cell_rows(cy)
                    ca, cb = src.cell_cols(c["x"])
                    truth = np.asarray(src.ground[north - src.pad:south - src.pad + 1,
                                                  ca - src.pad:cb - src.pad + 1], dtype=np.float64)[::-1]
                    err = np.abs(hm - truth)
                    lim = err > QUANT_M
                    limited_v += int(lim.sum())
                    all_max = max(all_max, float(err.max()))
                    if (~lim).any():
                        all_max_nolim = max(all_max_nolim, float(err[~lim].max()))
                    for (vx, vy) in pts.get((c["x"], cy), []):
                        sampled += 1
                        (sample_lim if lim[vy, vx] else sample_errs).append(float(err[vy, vx]))
                        probes.append({"pos": [c["x"] * su.CELL_UNITS + vx * su.VERTEX_SPACING_UNITS,
                                               cy * su.CELL_UNITS + vy * su.VERTEX_SPACING_UNITS],
                                       "groundM": round(float(truth[vy, vx]), 3),
                                       "landZ": round(float(h[vy, vx]) * su.VHGT_STEP_UNITS, 1),
                                       "limited": bool(lim[vy, vx])})
        for x, (h, n) in row.items():
            if x + 1 in row:
                edges += 1
                seam_h += int(not np.array_equal(h[:, -1], row[x + 1][0][:, 0]))
                seam_n += int(not np.array_equal(n[:, -1], row[x + 1][1][:, 0]))
            if x in prev:  # this cell's north edge (y = 32) is the north neighbour's south edge (y = 0)
                edges += 1
                seam_h += int(not np.array_equal(h[-1], prev[x][0]))
                seam_n += int(not np.array_equal(n[-1], prev[x][1]))
        prev = {x: (h[0], n[0]) for x, (h, n) in row.items()}
    res["heights"] = {
        "points_asked": a.points, "points_sampled": sampled,
        "max_error_m": round(max(sample_errs, default=0.0), 4),
        "points_limited": len(sample_lim), "max_error_limited_m": round(max(sample_lim, default=0.0), 3),
        "all_vertices_max_error_unlimited_m": round(all_max_nolim, 4),
        "all_vertices_limited": limited_v, "all_vertices_max_error_m": round(all_max, 3),
    }
    res["seams"] = {"edges": edges, "height": seam_h, "normal": seam_n}
    res["layers_max"] = max_layers
    res["overflow"] = {k: stats[k] for k in stats if k.startswith(("overflow", "limited", "max_limit", "limit_hist"))}
    res["cells"] = {k: stats[k] for k in ("cells", "province_cells", "apron_cells", "apron_skipped")}
    if res["heights"]["max_error_m"] > HEIGHT_TOL_M:
        fails.append(f"height error {res['heights']['max_error_m']} m > {HEIGHT_TOL_M} at unlimited points")
    if seam_h or seam_n:
        fails.append(f"seams: {seam_h} height, {seam_n} normal")
    if max_layers > su.LAND_QUADRANT_LAYERS:
        fails.append(f"{max_layers} layers in a quadrant")
    res["fails"] = fails
    (out / "probe-points.json").write_text(json.dumps(probes, indent=0) + "\n")  # the L4 heights scene reads these
    (out / "check.json").write_text(json.dumps(res, indent=1, sort_keys=True) + "\n")
    print(json.dumps(res, indent=1, sort_keys=True))
    return 1 if fails else 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="terrain", description=__doc__.split("\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--cells")
    b.add_argument("--out", default=str(OUT))
    b.add_argument("--no-apron", action="store_true")
    b.add_argument("--sample", action="store_true")
    w = sub.add_parser("world")
    w.add_argument("--out", default=str(OUT))
    c = sub.add_parser("check")
    c.add_argument("--out", default=str(OUT))
    c.add_argument("--points", type=int, default=1000)
    a = p.parse_args(argv)
    if a.cmd == "world":
        out = Path(a.out)
        print(world.write(out / "world.json", Sources.load().cell_range, out / "land"))
        return 0
    return cmd_build(a) if a.cmd == "build" else cmd_check(a)


if __name__ == "__main__":
    sys.exit(main())
