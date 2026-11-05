"""The hanging-edge census (lane 1.15-r6-water-edges): no water sheet's edge hangs in the air at a cell line.

A cell's water plane reaches its cell line. Where the neighbour across the line holds no water, or water lower than
the plane, the ground along the shared line must stand at or above the plane: a line vertex more than TOL_M under
the higher level shows the sheet's straight edge hanging over the slope (round 6 river-steps: step-2's upper plane
2.4 m over the lower cell's ground, its lower water 17 m below the foot). Skyrim.esm (probes/vanilla_hanging_edges.py,
2026-11-05): of its 762 wet/dry lines 2.0 % of the length hangs (under rocks and meshes); of its 77 level steps the
line stands a median 1.09 m over the upper level (the lip), 24 % of the length hanging at the falls' own faces,
each dressed by a falls mesh. So the bar: no hanging metre on a wet/dry or plain wet/wet line, and on a kept step
only inside its channel (the rapids line seated on it, steps.py).

The second census (lane 1.15-r6-water-edges-2), the lower water meeting a step's foot: for every kept step, the
vertices from the step line, down the channel's middle, to the first vertex under the lower cell's level (`foot`);
and every water cell's wet share (its vertices under its level) against its raster footprint (`wet`). Skyrim.esm
(probes/vanilla_hanging_edges.py): the lower water reaches the channel at vertex 0/8/33 (p10/50/90); round 6 had
(-48,16), (-59,-13), (-50,46) 0.0 % wet against 8-22 % footprints, buried by the bank lift. The bars: a kept
step's foot within FOOT_BAR vertices, and a cell's wet share at or above WET_SHARE of its footprint.

`python3 -m tools.argonia_world.water.edges_census [GROUND.npy]` prints the census as JSON; exit 1 on any red line
(the gate's `edges-census` item)."""
from __future__ import annotations

import numpy as np

from tools.argonia_world import skyrim_units as su

Q = su.QUADS_PER_CELL
TOL_M = 0.3  # the checks' freeboard: a line vertex more than this under the plane hangs
SEG_M = su.PROVINCE_SAMPLE_M
FOOT_BAR = 12  # vertices: vanilla's p50 8 plus our channel's graded bed (steps.foot_vertices, up to 4 at 21 m)
WET_SHARE = 0.8  # a cell keeps at least this share of its raster footprint wet
FOOT_RUN = 3  # vertices: the lower water meets the foot where this many in a row stand under it (a pool, not a pit)
FOOT_MIN = 0.05  # a footprint under this share of the cell (a fringe of the raster) is not counted
# the gate holds both measures at the landed counts of lane 1.15-r6-stepped-pools-2 (the pool-keep rule in
# water_field, roads and bridge seats exempt; scratch ground 2026-11-05): 83 of 203 kept steps with no lower water
# within FOOT_BAR of the line (was 183; Skyrim.esm: 36 of 77), 1,232 of 2,449 held cells under WET_SHARE of their
# footprint (was 1,654; most of the rest are blackwater bodies, a separate lane). More than these is red
FOOT_FAR_MAX = 83
BURIED_MAX = 1232


def step_foot(level: np.ndarray, ground: np.ndarray, s, cx0: int, cy0: int) -> int:
    """Vertices from step `s`'s line into its lower cell, down the channel's middle, to the first of FOOT_RUN
    vertices in a row under the lower level (Q + 1 when none in the cell): round 6's joined channel dug a one-vertex
    pit at its foot with the ground 10-17 m over the lower water past it."""
    C = level.shape[0]
    i, j = C - 1 - (s.cy - cy0), s.cx - cx0
    m = (s.cross_lo + s.cross_hi) // 2
    r, c = line_vertices(i, j, s.edge)
    r0, c0 = int(r[m]), int(c[m])
    di, dj = {"e": (0, 1), "w": (0, -1), "n": (-1, 0), "s": (1, 0)}[s.edge]
    k = np.arange(Q + 1)
    rr, cc = np.clip(r0 + di * k, 0, ground.shape[0] - 1), np.clip(c0 + dj * k, 0, ground.shape[1] - 1)
    return first_run(np.asarray(ground[rr, cc], np.float64) < s.lower_m)


def first_run(under: np.ndarray, run: int = FOOT_RUN) -> int:
    """The index of the first `run` True values in a row (len + 0 when none, capped at Q + 1)."""
    for k in range(len(under) - run + 1):
        if under[k:k + run].all():
            return k
    return Q + 1


def wet_shares(level: np.ndarray, ground: np.ndarray, foot: np.ndarray | None):
    """Per water cell (i, j): (wet share of its 32 x 32 vertices under its level, raster footprint share)."""
    C = level.shape[0]
    g = np.asarray(ground[:C * Q, :C * Q], np.float32).reshape(C, Q, C, Q).transpose(0, 2, 1, 3)
    wet = (g < level[:, :, None, None].astype(np.float32)).mean(axis=(2, 3))
    fp = None if foot is None else np.asarray(foot[:C * Q, :C * Q], bool).reshape(C, Q, C, Q).mean(axis=(1, 3))
    return wet, fp


def lines(level: np.ndarray):
    """Every cell line between a wet cell and a drier neighbour: (i, j, edge, upper, other) in the level grid's
    [row from north, column from west]; `other` NaN when the neighbour is dry."""
    for di, dj, e in ((0, 1, "e"), (0, -1, "w"), (1, 0, "s"), (-1, 0, "n")):
        for i, j in zip(*np.nonzero(np.isfinite(level))):
            a, b = i + di, j + dj
            if not (0 <= a < level.shape[0] and 0 <= b < level.shape[1]):
                continue
            up, ot = float(level[i, j]), float(level[a, b])
            if np.isfinite(ot) and ot >= up - TOL_M:
                continue
            yield int(i), int(j), e, up, ot


def line_vertices(i: int, j: int, edge: str):
    """The shared line's Q+1 vertices as (rows, cols), indexed as a step's cross range (0..Q): south to north on an
    e/w edge, west to east on an n/s edge."""
    k = np.arange(Q + 1)
    if edge in ("e", "w"):
        col = (j + 1) * Q if edge == "e" else j * Q
        return (i * Q + Q - k, np.full(Q + 1, col))
    row = i * Q if edge == "n" else (i + 1) * Q
    return (np.full(Q + 1, row), j * Q + k)


def census(level: np.ndarray, ground: np.ndarray, steps=(), cx0: int = su.PROVINCE_CELL_SW[0],
           cy0: int = su.PROVINCE_CELL_SW[1], foot: np.ndarray | None = None, held: np.ndarray | None = None) -> dict:
    """The hanging metres per line, split into a kept step's channel and everything else (the red)."""
    C = level.shape[0]
    chan = {}
    for s in steps:
        if s.chain != "closed" and s.cross_lo >= 0:
            chan[(C - 1 - (s.cy - cy0), s.cx - cx0, s.edge)] = (s.cross_lo, s.cross_hi)
    rows = []
    tot = {"step": 0.0, "other": 0.0, "lines": 0}
    for i, j, e, up, ot in lines(level):
        tot["lines"] += 1
        g = ground[line_vertices(i, j, e)].astype(np.float64)
        seg = (g[1:] + g[:-1]) / 2 < up - TOL_M
        if not seg.any():
            continue
        k = np.arange(Q)
        lo, hi = chan.get((i, j, e), (Q + 1, -1))
        inch = (k + 1 >= lo) & (k <= hi)  # the channel and its two side walls
        m_step, m_other = float((seg & inch).sum()) * SEG_M, float((seg & ~inch).sum()) * SEG_M
        tot["step"] += m_step
        tot["other"] += m_other
        rows.append({"cell": [int(j + cx0), int(C - 1 - i + cy0)], "edge": e, "upper_m": round(up, 2),
                     "other_m": None if not np.isfinite(ot) else round(ot, 2), "step_m": round(m_step, 1),
                     "other_hanging_m": round(m_other, 1), "depth_m": round(up - float(g.min()), 2)})
    rows.sort(key=lambda r: -r["other_hanging_m"])
    red = [r for r in rows if r["other_hanging_m"] > 0]
    kept = [s for s in steps if s.chain != "closed" and s.cross_lo >= 0]
    feet = [(step_foot(level, ground, s, cx0, cy0), s) for s in kept]
    far = sorted(((f, s) for f, s in feet if f > FOOT_BAR), key=lambda t: -t[0])
    fv = [f for f, _ in feet]
    wet, fp = wet_shares(level, ground, foot)
    buried = []
    own = np.isfinite(level) if held is None else np.isfinite(level) & held
    if fp is not None:
        for i, j in zip(*np.nonzero(own & (fp >= FOOT_MIN) & (wet < WET_SHARE * fp))):
            buried.append({"cell": [int(j + cx0), int(C - 1 - i + cy0)], "level_m": round(float(level[i, j]), 2),
                           "wet": round(float(wet[i, j]), 3), "footprint": round(float(fp[i, j]), 3)})
        buried.sort(key=lambda r: r["wet"] - r["footprint"])
    out = {"foot_steps": len(kept), "foot_p10_50_90": np.percentile(fv, [10, 50, 90]).round(1).tolist() if fv else [],
           "foot_far": len(far), "foot_worst": [{"cell": [s.cx, s.cy], "edge": s.edge, "drop_m": round(s.upper_m - s.lower_m, 2),
                                               "foot": f} for f, s in far[:20]],
           "wet_cells": int((own & (fp >= FOOT_MIN)).sum()) if fp is not None else 0,
           "buried_cells": len(buried), "buried_worst": buried[:20]}
    return {**out, "lines": tot["lines"], "hanging_lines": len(rows), "red_lines": len(red),
            "step_hanging_m": round(tot["step"], 1), "other_hanging_m": round(tot["other"], 1),
            "worst": red[:20], "worst_steps": sorted(rows, key=lambda r: -r["step_m"])[:20]}


STAMP_Q = ("SELECT cx, cy, level_m, water_type, body_id, reach_id FROM cell_water ORDER BY cx, cy",
           "SELECT * FROM water_step ORDER BY cx, cy, edge",
           "SELECT id, kind, level_from_m, level_to_m, width_m, cell_kind FROM hydrology_reach ORDER BY id",
           "SELECT reach_id, ord, east_m, south_m FROM hydrology_reach_point ORDER BY reach_id, ord")


def stamp(ground, w) -> str:
    """What the census reads: its code, the ground's bytes, the frozen body raster's, and the solved water rows."""
    import hashlib
    from pathlib import Path

    from tools.argonia_world.terrain import cellwater
    from tools.argonia_world.terrain.grid import data_root
    h = hashlib.sha256()
    for p in (Path(__file__), Path(cellwater.__file__), Path(ground), data_root() / "hydrology-graph-bodies.npz"):
        h.update(p.name.encode())
        h.update(p.read_bytes())
    for q in STAMP_Q:
        h.update(repr([tuple(r) for r in w.query(q)]).encode())
    return h.hexdigest()


def main(argv=None) -> int:
    import argparse
    import json
    from pathlib import Path

    from tools.argonia_world import db
    from tools.argonia_world.terrain import cellwater
    from tools.argonia_world.terrain.grid import generated_ground

    ap = argparse.ArgumentParser()
    ap.add_argument("ground", nargs="?")
    a = ap.parse_args(argv)
    gp = Path(a.ground or generated_ground())
    w = db.open()
    st = stamp(gp, w)
    cache = gp.parent / "edges-census.json"  # the result cached by its stamp
    res = None
    try:
        old = json.loads(cache.read_text())
        res = old if old.get("stamp") == st else None
    except (OSError, ValueError):
        res = None
    if res is None:
        cw = cellwater.load(w)
        lev, _ = cellwater.wet_raster(w)
        res = {"stamp": st, **census(cw.level, np.load(gp, mmap_mode="r"), cw.steps, foot=~np.isnan(lev), held=cw.held)}
        try:
            cache.write_text(json.dumps(res, indent=1) + "\n")
        except OSError:
            pass
    print(json.dumps(res, indent=1))
    return 1 if red(res) else 0


def red(res: dict) -> bool:
    """The gate: any hanging line, or either second-census measure over its held ceiling."""
    return bool(res["red_lines"]) or res["foot_far"] > FOOT_FAR_MAX or res["buried_cells"] > BURIED_MAX


if __name__ == "__main__":
    raise SystemExit(main())
