"""Probe (0034, lane 1.15-r6-water-edges): does Skyrim.esm's water sheet ever hang at a cell line?

For every pair of 4-adjacent Tamriel cells where at least one carries an explicit water level (XCLW, has-water flag),
along the shared line (the 33 shared vertices): H the higher level, the line's metres where the ground stands more
than 0.3 m (21 u) under H (a hanging sheet edge), split by the pair's kind: wet/dry (the neighbour has no explicit
level) and step (both wet, levels > 64 u apart). For the steps also: the line's ground over the upper level
(p10/50/90) and the face's run, the vertices into the lower cell until its ground is under the lower level.
Usage: python3 -m tools.argonia_world.terrain.probes.vanilla_hanging_edges [Skyrim.esm]  (reads only; prints JSON)"""
import json
import struct
import sys
from pathlib import Path

import numpy as np

from tools.argonia_world import skyrim_units as su
from tools.argonia_world.terrain.esm import records
from tools.argonia_world.terrain.probes.vanilla_lake_cells import TAMRIEL, vhgt
from tools.argonia_world.water.edges_census import first_run

ESM = Path(sys.argv[1] if len(sys.argv) > 1 else "/home/ubuntu/games/skyrimse/Data/Skyrim.esm")
TOL_U = 21.0  # 0.3 m
SEG_M = su.VERTEX_SPACING_UNITS / su.UNITS_PER_METRE


def load():
    water, land, wrld, cell = {}, {}, None, None
    for r in records(ESM.read_bytes()):
        if r.sig == "WRLD":
            wrld = r.formid
        elif r.sig == "CELL":
            xc = r.first("XCLC")
            cell = struct.unpack_from("<ii", xc) if (xc and wrld == TAMRIEL) else None
            if cell is not None:
                w, d = r.first("XCLW"), r.first("DATA")
                if w and d and d[0] & 2:
                    h = struct.unpack_from("<f", w)[0]
                    if -1e6 < h < 1e6:
                        water[cell] = h
        elif r.sig == "LAND" and cell is not None and cell not in land:
            v = r.first("VHGT")
            if v:
                land[cell] = vhgt(v)
    return water, land


def strip(g, side):
    """The cell's vertices from the `side` line inward: (33 along, 33 in). Rows run south to north."""
    return {"e": g[:, ::-1], "w": g, "n": g[::-1, :].T, "s": g.T}[side]


def main():
    water, land = load()
    out = {"wet_dry": [0.0, 0.0], "step": [0.0, 0.0]}  # [hanging m, line m]
    chain, foot_run = [], []
    lip, run, worst, face, foot = [], [], [], [], []
    drops, over, lower_wet, uppers = [], [], [], set()
    for (x, y), _ in list(water.items()):
        for dx, dy, se, so in ((1, 0, "e", "w"), (-1, 0, "w", "e"), (0, 1, "n", "s"), (0, -1, "s", "n")):
            o = (x + dx, y + dy)
            if (x, y) not in land or o not in land:
                continue
            hu = water[(x, y)]
            ho = water.get(o)
            if ho is not None and ho >= hu - 64:
                continue  # the other side is the upper one or the same water: counted from there or no edge
            kind = "step" if ho is not None else "wet_dry"
            e = strip(land[o], so)[:, 0]
            seg = (e[1:] + e[:-1]) / 2 < hu - TOL_U
            out[kind][0] += float(seg.sum()) * SEG_M
            out[kind][1] += 32 * SEG_M
            if seg.any():
                worst.append((float(seg.sum()) * SEG_M, (x, y), se, kind, round(float(hu - e.min()) / su.UNITS_PER_METRE, 2)))
            if kind == "step":
                lip.append(float(np.median(e - hu)) / su.UNITS_PER_METRE)
                s = strip(land[o], so)
                under = s < ho
                run.append(float(np.median([np.argmax(r) if r.any() else 33 for r in under])))
                # the face at the channel (the line's lowest vertex): the lower cell's ground by vertex in, over the
                # lower level (m), and whether the lower water reaches it (vertices to the first under-level vertex)
                r0 = int(np.argmin(e))
                face.append(((s[r0, :9] - ho) / su.UNITS_PER_METRE).round(1).tolist())
                foot.append(int(np.argmax(under[r0])) if under[r0].any() else 33)
                foot_run.append(first_run(under[r0]))
                # the bar for a bank: the step line's ground over the upper level off the channel (vanilla's lift), the
                # drop, the lower cell's wet share (vertices under its level), and whether the lower cell steps again
                drops.append(float(hu - ho) / su.UNITS_PER_METRE)
                over.append(float(np.max(e - hu)) / su.UNITS_PER_METRE)
                lower_wet.append(float((land[o] < ho).mean()))
                uppers.add((x, y))
                chain.append(o)
    again = sum(1 for o in chain if o in uppers)
    q = lambda a: np.percentile(a, [10, 50, 90]).round(2).tolist() if a else []
    worst.sort(reverse=True)
    print(json.dumps({
        "water_cells": len(water),
        "wet_dry": {"lines": int(out["wet_dry"][1] / 32 / SEG_M), "hanging_m": round(out["wet_dry"][0], 1),
                    "share": round(out["wet_dry"][0] / max(out["wet_dry"][1], 1), 4)},
        "step": {"lines": len(lip), "hanging_m": round(out["step"][0], 1),
                 "share": round(out["step"][0] / max(out["step"][1], 1), 4),
                 "line_over_upper_m_p10_50_90": q(lip), "face_run_vertices_p10_50_90": q(run),
                 "channel_face_over_lower_m_by_vertex_p50": np.median(face, 0).round(2).tolist() if face else [],
                 "channel_foot_vertices_p10_50_90": q(foot),
                 "channel_foot_run3_vertices_p10_50_90": q(foot_run),
                 "channel_foot_run3_within_12": f"{sum(f <= 12 for f in foot_run)} of {len(foot_run)}",
                 "drop_m_p10_50_90_max": q(drops) + [round(max(drops), 2)] if drops else [],
                 "line_max_over_upper_m_p50_90_max": np.percentile(over, [50, 90, 100]).round(2).tolist() if over else [],
                 "lower_wet_share_p10_50_90": q(lower_wet),
                 "lower_steps_again": f"{again} of {len(chain)}"},
        "worst": [{"m": round(m, 1), "cell": c, "edge": e, "kind": k, "depth_m": d} for m, c, e, k, d in worst[:20]],
    }, indent=1))


if __name__ == "__main__":
    main()
