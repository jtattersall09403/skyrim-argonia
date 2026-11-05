"""The hanging-edge census (lane 1.15-r6-water-edges): no water sheet's edge hangs in the air at a cell line.

A cell's water plane reaches its cell line. Where the neighbour across the line holds no water, or water lower than
the plane, the ground along the shared line must stand at or above the plane: a line vertex more than TOL_M under
the higher level shows the sheet's straight edge hanging over the slope (round 6 river-steps: step-2's upper plane
2.4 m over the lower cell's ground, its lower water 17 m below the foot). Skyrim.esm (probes/vanilla_hanging_edges.py,
2026-11-05): of its 762 wet/dry lines 2.0 % of the length hangs (under rocks and meshes); of its 77 level steps the
line stands a median 1.09 m over the upper level (the lip), 24 % of the length hanging at the falls' own faces,
each dressed by a falls mesh. So the bar: no hanging metre on a wet/dry or plain wet/wet line, and on a kept step
only inside its channel (the rapids line seated on it, steps.py).

`python3 -m tools.argonia_world.water.edges_census [GROUND.npy]` prints the census as JSON; exit 1 on any red line
(the gate's `edges-census` item)."""
from __future__ import annotations

import numpy as np

from tools.argonia_world import skyrim_units as su

Q = su.QUADS_PER_CELL
TOL_M = 0.3  # the checks' freeboard: a line vertex more than this under the plane hangs
SEG_M = su.PROVINCE_SAMPLE_M


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
           cy0: int = su.PROVINCE_CELL_SW[1]) -> dict:
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
    return {"lines": tot["lines"], "hanging_lines": len(rows), "red_lines": len(red),
            "step_hanging_m": round(tot["step"], 1), "other_hanging_m": round(tot["other"], 1),
            "worst": red[:20], "worst_steps": sorted(rows, key=lambda r: -r["step_m"])[:20]}


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
    cw = cellwater.load(db.open())
    h = np.load(Path(a.ground or generated_ground()), mmap_mode="r")
    res = census(cw.level, h, cw.steps)
    print(json.dumps(res, indent=1))
    return 1 if res["red_lines"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
