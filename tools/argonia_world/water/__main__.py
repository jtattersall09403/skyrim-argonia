"""The water solve and its L1 gate (1.15 §a, decision 0033 §1).

    python3 -m tools.argonia_world.water solve      solve every body and reach to one level per cell; write
                                                    cell_water, water_step and hydrology_reach.cell_kind (db.py)
    python3 -m tools.argonia_world.water check      re-solve in memory and check the database against it: every
                                                    body with a cell or a recorded drop, one level per cell, every
                                                    step with a chain. Exit 1 on a failure. (`make world`)
    python3 -m tools.argonia_world.water emit [--out out/water] [--index out/pieces-index.json]
                                                    the ESM writer's stream from the database: records.json (WATR),
                                                    cells.jsonl (XCLW/XCWT and the step pieces as refs), plan.json
    python3 -m tools.argonia_world.water records    the WATR intermediate records as JSON

Reads the hydrology through db.py and the frozen body raster in $ARGONIA_DATA.
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def _summary(res) -> dict:
    from tools.argonia_world.water import solve as sv
    return {
        "cells": len(res.cells),
        "byType": dict(sorted(collections.Counter(v[1] for v in res.cells.values()).items())),
        "steps": dict(sorted(collections.Counter(s.chain for s in res.steps).items())),
        "dryReaches": res.dry,
        "reaches": dict(collections.Counter(res.reach_kind.values())),
        "bodies": dict(collections.Counter(o.split(":")[0].split(" ")[0] for o in res.body_outcome.values())),
        "contestedCells": res.contested,
        "enclosedCells": res.enclosed,
        "wallCells": res.walls,
        "seconds": round(res.seconds, 2),
        "snap": [sv.SNAP_LO_M, sv.SNAP_HI_M],
    }


def cmd_solve() -> int:
    from tools.argonia_world import db
    from tools.argonia_world.water import solve as sv
    w = db.open()
    res = sv.solve(w)
    sv.write(w, res)
    print(json.dumps(_summary(res)))
    return 0


def cmd_check() -> int:
    from tools.argonia_world import db
    from tools.argonia_world.water import solve as sv
    from tools.argonia_world.water import steps as stp
    t0 = time.time()
    w = db.open()
    res = sv.solve(w)
    bad: list[str] = []
    have = {(r[0], r[1]): (r[2], r[3], r[4], r[5]) for r in w.query(
        "SELECT cx, cy, level_m, water_type, body_id, reach_id FROM cell_water")}
    if have != res.cells:
        diff = set(have.items()) ^ set(res.cells.items())
        bad.append(f"cell_water is stale against the solve ({len(diff)} rows differ): run `water solve`")
    two = len(w.query("SELECT cx, cy FROM cell_water GROUP BY cx, cy HAVING count(DISTINCT level_m) > 1"))
    steps = w.query("SELECT cx, cy, edge, chain, upper_m, lower_m FROM water_step")
    unchained = [tuple(s) for s in steps if s[3] not in stp.CHAINS and s[3] != "closed"]
    if len(steps) != len(res.steps):
        bad.append(f"water_step has {len(steps)} rows, the solve {len(res.steps)}: run `water solve`")
    bodies = w.values("SELECT id FROM hydrology_body")
    no_outcome = [b for b in bodies if b not in res.body_outcome]
    kinds = {r[0]: r[1] for r in w.query("SELECT id, cell_kind FROM hydrology_reach")}
    stale_kind = [r for r, k in res.reach_kind.items() if kinds.get(r) != k]
    drops = sum(1 for o in res.body_outcome.values() if o.startswith("drop"))
    print(f"water check: {len(bodies)} bodies, {len(bodies) - drops - len(no_outcome)} with cells, {drops} recorded "
          f"drops, {len(no_outcome)} with neither; {len(have)} cells, {two} with two levels; {len(steps)} steps, "
          f"{len(unchained)} without a chain; {len(res.dry)} dry reaches; {time.time() - t0:.1f} s")
    if no_outcome:
        bad.append(f"{len(no_outcome)} bodies with no outcome: {no_outcome[:5]}")
    if two:
        bad.append(f"{two} cells with two levels")
    if unchained:
        bad.append(f"{len(unchained)} steps without a chain: {unchained[:3]}")
    if stale_kind:
        bad.append(f"{len(stale_kind)} reaches' cell_kind stale: run `water solve`")
    for b in bad:
        print("water check red:", b)
    return 1 if bad else 0


def cmd_emit(out: Path, index_path: Path) -> int:
    """cells.jsonl for WaterRecords.ApplyCell: per water cell its height and type; per step its chain's pieces."""
    from tools.argonia_world import db
    from tools.argonia_world import pieces as pz
    from tools.argonia_world import skyrim_units as su
    from tools.argonia_world.water import layer
    from tools.argonia_world.water import solve as sv
    from tools.argonia_world.water import steps as stp
    w = db.open()
    cw = sv.load(w)
    resolver = pz.Resolver(pz.Index.load(index_path))
    resolved = {k: resolver.resolve(m)[0] for k, (m, _, _) in stp.PIECES.items()}
    unresolved = sorted(k for k, r in resolved.items() if r.kind != "base")
    widths = {(r[0], r[1]): r[2] for r in w.query(
        "SELECT c.cx, c.cy, r.width_m FROM cell_water c JOIN hydrology_reach r ON r.id = c.reach_id")}
    lines: dict[tuple[int, int], dict] = {}
    for (cx, cy), (lv, wt) in cw._cells.items():
        lines[(cx, cy)] = {"x": cx, "y": cy, "waterHeight": su.rounded(su.metres_to_units(lv), 2),
                           "waterType": layer.type_key(wt), "refs": []}
    yaw = {"n": 0.0, "e": 90.0, "s": 180.0, "w": 270.0}
    sample = None
    for s in cw.steps():
        if s.chain == "closed":
            continue
        ox, oy = su.cell_origin(s.cx, s.cy)
        mid = (s.cross_lo + s.cross_hi) / 2 * su.VERTEX_SPACING_UNITS
        x, y = {"n": (ox + mid, oy + su.CELL_UNITS), "s": (ox + mid, oy), "e": (ox + su.CELL_UNITS, oy + mid),
                "w": (ox, oy + mid)}[s.edge]
        width_m = widths.get((s.cx, s.cy)) or (s.cross_hi - s.cross_lo) * su.PROVINCE_SAMPLE_M
        drop = s.upper_m - s.lower_m
        line = lines.setdefault((s.cx, s.cy), {"x": s.cx, "y": s.cy, "refs": []})
        for k in stp.CHAINS[s.chain]:
            if resolved[k].kind != "base":
                continue
            _, wu, hu = stp.PIECES[k]
            size = su.metres_to_units(drop) / hu if k in stp.SCALE_BY_DROP else su.metres_to_units(width_m) / wu
            z = s.lower_m if k in stp.AT_FOOT else s.upper_m
            line["refs"].append({"base": resolved[k].form_key,
                                 "pos": [su.rounded(x, 2), su.rounded(y, 2), su.rounded(su.metres_to_units(z), 2)],
                                 "rot": [su.rounded(v, 6) for v in su.yaw_to_rot(yaw[s.edge])],
                                 "scale": su.rounded(min(10.0, max(0.1, size)), 4)})
        if sample is None and s.chain == "falls":
            sample = s
    over = []
    for (cx, cy), line in lines.items():
        if len(line["refs"]) > layer.REFS_PER_CELL:
            over.append(f"({cx},{cy})")
            line["refs"] = line["refs"][:layer.REFS_PER_CELL]
        for k, r in enumerate(line["refs"]):
            r["formKey"] = layer.ref_key(cx, cy, k)
    out.mkdir(parents=True, exist_ok=True)
    (out / "cells.jsonl").write_text("".join(json.dumps(v, separators=(",", ":")) + "\n" for _, v in
                                             sorted(lines.items(), key=lambda kv: (kv[0][1], kv[0][0]))))
    (out / "records.json").write_text(json.dumps({"schema": 1, "records": layer.records()}, indent=1) + "\n")
    plan = {"cells": len(lines), "pieces": sum(len(v["refs"]) for v in lines.values()), "unresolved": unresolved,
            "overSlot": over}
    if sample is not None:  # a falls step for the world sample's river stop
        plan["sampleStep"] = {"cell": [sample.cx, sample.cy], "edge": sample.edge, "upperM": sample.upper_m,
                              "lowerM": sample.lower_m, "chain": sample.chain}
    (out / "plan.json").write_text(json.dumps(plan, indent=1) + "\n")
    print(f"water emit: {plan['cells']} cells, {plan['pieces']} piece refs, unresolved {unresolved}, "
          f"over slot {len(over)}")
    return 1 if unresolved or over else 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="water", description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=["solve", "check", "emit", "records"])
    ap.add_argument("--out", default=str(ROOT / "out" / "water"))
    ap.add_argument("--index", default=str(ROOT / "out" / "pieces-index.json"))
    a = ap.parse_args(argv)
    if a.cmd == "records":
        from tools.argonia_world.water import layer
        print(json.dumps(layer.records(), indent=1, sort_keys=True))
        return 0
    if a.cmd == "solve":
        return cmd_solve()
    if a.cmd == "check":
        return cmd_check()
    return cmd_emit(Path(a.out), Path(a.index))


if __name__ == "__main__":
    sys.exit(main())
