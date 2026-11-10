"""The water as the game reads it, as verify.py rows (walk 5, items G, H and the water's edge).

Everything is measured by `ArgoniaPlugin waterstudy check` on the built ESM (every cell's XCWT resolved to the record
the game shows, every LAND decoded as the game decodes VHGT), never on the writer's inputs:
- per kind, the share of its cells that look nearer their own kind than any other, and the share within one seam
  step of their own look; the kinds' own looks' nearest pair;
- each flowing cell's current and surface drift against the channel graph's heading (water_flow_cells.json), and the
  drift convention itself on Update.esm's directional river and creek records;
- still water's current; the look's step at every edge between two water cells;
- land vertices against the water plane.
How each threshold was set: docs/research/nw-02-walk5-water.md.
"""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

FIGHT = 8.0          # units: one VHGT step; a vertex nearer the plane than this fights with it
MIN_PAIR = 40.0      # of 255: two kinds' own looks; Skyrim's DefaultWater against DefaultMarshWater, the closest pair it ships as different waters
READS_AS_OWN = 0.5   # a kind's cells that look nearer their own kind than any other: the typical cell reads as its kind
FLOW_TOL = 22.5      # degrees: half a step of Skyrim's eight-way flow records
CONVENTION_TOL = 45.0  # degrees: vanilla's own directional records sit 7-23 off their current; a wrong convention 90-180
STEP_P99, STEP_MAX = 14.0, 14.0   # of 255: the look's step at a cell edge, the owner's smooth seams (2026-11-09)


def esm_check(bin_dll: Path, plugin: Path, data: Path, flow_json: Path, out: Path) -> dict:
    env = dict(os.environ, DOTNET_ROOT=str(Path.home() / ".dotnet"), DOTNET_CLI_TELEMETRY_OPTOUT="1", DOTNET_NOLOGO="1")
    env["PATH"] = f"{Path.home() / '.dotnet'}:{env['PATH']}"
    res = out / "water_check.json"
    subprocess.run(["dotnet", str(bin_dll), "waterstudy", "check", str(plugin / "ArgoniaNewWorld.esm"), str(data),
                    str(plugin / "cells.json"), str(flow_json), str(res)], check=True, env=env, capture_output=True)
    return json.loads(res.read_text())


def rows(rep, chk: dict) -> None:
    """The water rows from a waterstudy check result."""
    for k, v in sorted(chk["kinds"].items()):
        rep.row("water", f"{k}: its cells read as {k} (nearer its own look than any other kind's) in >= {READS_AS_OWN:.0%}",
                {"reads_as_own": v["reads_as_own_share"], "near_own": v["near_own_share"], "pure": v["pure_share"], "cells": v["cells"]},
                v["reads_as_own_share"] >= READS_AS_OWN,
                f"median distance from its own look {v['own_distance_median']} of 255; mean look {v['mean_look']}"
                + ("" if v["own_distance_median"] >= 0 else "; no record of its own in the ESM"))
    pairs = chk["own_look_pairs"]
    rep.row("water", f"every two kinds' own looks differ by >= {MIN_PAIR:g} of 255", chk["own_look_min_pair"],
            bool(pairs) and chk["own_look_min_pair"] >= MIN_PAIR, f"nearest {pairs[:3]}")
    n = chk["flowing_cells"]
    ok = n > 0 and chk["velocity_within_22_5"] == n and chk["noise_within_22_5"] == n
    rep.row("water", f"flowing cells run with the channel graph (current and surface drift within {FLOW_TOL:g} degrees)",
            f"{min(chk['velocity_within_22_5'], chk['noise_within_22_5'])}/{n}", ok,
            f"error p50/p90/max: current {chk['velocity_err_p50_p90_max']}, drift {chk['noise_err_p50_p90_max']}; "
            + "; ".join(chk["flow_examples_off"][:3]))
    conv = chk.get("convention") or {}
    rep.row("water", f"the drift convention holds on Update.esm's river and creek records (drift within {CONVENTION_TOL:g} of their current)",
            {k: v[2] for k, v in conv.items()}, len(conv) == 4 and all(v[2] <= CONVENTION_TOL for v in conv.values()),
            "; ".join(f"{k}: current {v[0]}, drift {v[1]}" for k, v in conv.items()))
    rep.row("water", "still water (sea, swamp, marsh, pond, still estuary) has no current",
            f"{chk['still_cells_with_flow']} of {chk['still_cells']}", chk["still_cells"] > 0 and chk["still_cells_with_flow"] == 0)
    p50, p99, mx = chk["edge_step_p50_p99_max"]
    rep.row("water", f"seams smooth: the look's step at a cell edge p99 <= {STEP_P99:g}, max <= {STEP_MAX:g} of 255",
            [p50, p99, mx], p99 <= STEP_P99 and mx <= STEP_MAX, f"{chk['edge_steps']} edges that change")
    sh = chk.get("shore")
    if not sh:
        rep.fail("water", f"no land vertex within the fighting band (|z - water| < {FIGHT:g} units)", "no LAND read from the ESM")
        return
    rep.row("water", f"no land vertex within the fighting band (|z - water| < {FIGHT:g} units)", sh["within_fight_band"],
            sh["within_fight_band"] == 0,
            f"{sh['on_plane']} on the plane; {sh['vertices_near']} within 64 units; rise across a shore edge "
            f"p10/median/p90 {sh['rise_p10_median_p90']} (Skyrim.esm's sea shores 8/32/104, Hjaalmarch 8/24/48)")
