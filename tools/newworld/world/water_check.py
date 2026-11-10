"""The water as the game reads it, as verify.py rows (walk 5, items G, H and the water's edge).

    python3 -m tools.newworld.world.water_check [--plugin out/newworld/plugin]   # the land rows alone, printed

Kinds, flow and seams are measured by `ArgoniaPlugin waterstudy check` on the built ESM (every cell's XCWT resolved
to the record the game shows): per kind, the share of cells carrying the kind's own record and the mean look (shallow,
deep and reflection colours and opacity); the distance between kinds as seen; each flowing cell's current and surface
drift against the channel graph's heading (water_flow_cells.json); still kinds' current; the look's step at every
edge between two water cells.

The land rows read the land shards the ESM was written from (tools/newworld/world/land.py), decoded as the game
decodes VHGT: no land vertex may sit within one height step (8 units) of the water plane, where land and water
would fight for the same pixels; Skyrim.esm's own shores were measured for the rule (docs/research/nw-02-walk5-water.md).
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np

V = 33
FIGHT = 8.0                 # units: one VHGT step; a vertex nearer the plane than this fights with it
MIN_PAIR = 15.0             # of 255: the nearest two kinds' mean looks must differ by at least this
BROAD = ("sea", "blackwater-swamp", "green-marsh", "pond")   # kinds wide enough to keep their own record inside
BROAD_PURE = 0.10           # the least share of a broad kind's cells carrying its own record
FLOW_TOL = 22.5             # degrees: a flowing cell's current and drift against the channel graph
STEP_P99, STEP_MAX = 24.0, 40.0   # of 255: the look's step at a cell edge (an 11-cell seam over the kinds' contrasts)


def heights(raw: bytes) -> np.ndarray:
    """One cell's 33 x 33 vertex heights (world units, [y from the south][x]) from its shard bytes (offset, deltas)."""
    off = np.frombuffer(raw[:4], np.float32)[0]
    d = np.frombuffer(raw[4:4 + V * V], np.int8).reshape(V, V).astype(np.float64)
    rows = off + np.cumsum(d[:, 0])
    z = rows[:, None] + np.concatenate([np.zeros((V, 1)), np.cumsum(d[:, 1:], axis=1)], axis=1)
    return z * 8


def shore(plugin: Path) -> dict:
    """Land vertices against the water plane over every cell: how many within the fighting band, how many exactly on
    it, and the rise across each grid edge that crosses the plane (units per 128) in cells the shore crosses."""
    man = json.loads((plugin / "land/manifest.json").read_text())
    water, nx, cb = float(man["grid"]["water"]), man["grid"]["cells_x"], man["cell_bytes"]
    near = fight = on = 0
    rises = []
    for name in man["shards"]:
        buf = (plugin / "land" / name).read_bytes()
        for i in range(nx):
            dz = heights(buf[i * cb:(i + 1) * cb]) - water
            a = np.abs(dz)
            near += int((a <= 64).sum())
            fight += int((a < FIGHT).sum())
            on += int((dz == 0).sum())
            below = dz <= 0
            if below.all() or not below.any():
                continue
            for x, y in ((np.diff(dz, axis=1), below[:, 1:] != below[:, :-1]), (np.diff(dz, axis=0), below[1:] != below[:-1])):
                rises.append(np.abs(x[y]))
    r = np.concatenate(rises) if rises else np.zeros(0)
    pct = (lambda q: float(np.percentile(r, q))) if len(r) else (lambda q: 0.0)
    return {"vertices_near": near, "within_fight_band": fight, "on_plane": on, "crossing_edges": int(len(r)),
            "rise_p10_median_p90": [pct(10), pct(50), pct(90)]}


def esm_check(bin_dll: Path, plugin: Path, data: Path, flow_json: Path, out: Path) -> dict:
    env = dict(os.environ, DOTNET_ROOT=str(Path.home() / ".dotnet"), DOTNET_CLI_TELEMETRY_OPTOUT="1", DOTNET_NOLOGO="1")
    env["PATH"] = f"{Path.home() / '.dotnet'}:{env['PATH']}"
    res = out / "water_check.json"
    subprocess.run(["dotnet", str(bin_dll), "waterstudy", "check", str(plugin / "ArgoniaNewWorld.esm"), str(data),
                    str(plugin / "cells.json"), str(flow_json), str(res)], check=True, env=env, capture_output=True)
    return json.loads(res.read_text())


def rows(rep, chk: dict, sh: dict) -> None:
    """The water rows from a waterstudy check result and the shore stats."""
    kinds = chk["kinds"]
    near = {k: min((d for a, b, d in chk["pairs"] if k in (a, b)), default=255.0) for k in kinds}
    for k, v in sorted(kinds.items()):
        broad = k in BROAD
        ok = near[k] >= MIN_PAIR and (not broad or v["pure_share"] >= BROAD_PURE)
        rep.row("water", f"{k}: distinct as seen (nearest kind >= {MIN_PAIR:g} of 255)"
                + (f", own record in >= {BROAD_PURE:.0%} of its cells" if broad else ""),
                {"nearest": near[k], "pure_share": v["pure_share"], "cells": v["cells"]}, ok,
                f"mean look (shallow, deep, reflection rgb, opacity) {v['mean_look']}; {v['pure']} cells carry its own record")
    n = chk["flowing_cells"]
    ok = n > 0 and chk["velocity_within_22_5"] == n and chk["noise_within_22_5"] == n
    rep.row("water", f"flowing cells run with the channel graph (current and surface drift within {FLOW_TOL:g} degrees)",
            f"{min(chk['velocity_within_22_5'], chk['noise_within_22_5'])}/{n}", ok,
            f"error p50/p90/max: current {chk['velocity_err_p50_p90_max']}, drift {chk['noise_err_p50_p90_max']}; "
            + "; ".join(chk["flow_examples_off"][:3]))
    rep.row("water", "still kinds (sea, swamp, marsh, pond) have no current", f"{chk['still_cells_with_flow']} of {chk['still_cells']}",
            chk["still_cells"] > 0 and chk["still_cells_with_flow"] == 0)
    p50, p99, mx = chk["edge_step_p50_p99_max"]
    rep.row("water", f"seams gradual: the look's step at a cell edge p99 <= {STEP_P99:g}, max <= {STEP_MAX:g} of 255",
            [p50, p99, mx], p99 <= STEP_P99 and mx <= STEP_MAX, f"{chk['edge_steps']} edges that change")
    rep.row("water", f"no land vertex within the fighting band (|z - water| < {FIGHT:g} units)", sh["within_fight_band"],
            sh["within_fight_band"] == 0,
            f"{sh['on_plane']} on the plane; {sh['vertices_near']} within 64 units; rise across a shore edge "
            f"p10/median/p90 {sh['rise_p10_median_p90']} (Skyrim.esm's sea shores 8/32/104, Hjaalmarch 8/24/48)")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--plugin", type=Path, default=Path(__file__).resolve().parents[3] / "out/newworld/plugin")
    print(json.dumps(shore(ap.parse_args(argv).plugin)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
