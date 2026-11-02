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
import math
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


def cmd_check(water_out: Path, index_path: Path, ground_path: Path) -> int:
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
    bad += placement(w, sv.load(w), water_out, index_path, ground_path)
    for b in bad:
        print("water check red:", b)
    return 1 if bad else 0


def placement(w, cw, water_out: Path, index_path: Path, ground_path: Path) -> list[str]:
    """The three placement rules (judge.py) on the emitted stream and the written ground; each part skips, saying
    so, where its input is not built here."""
    import numpy as np
    from tools.argonia_world import pieces as pz
    from tools.argonia_world import skyrim_units as su
    from tools.argonia_world.water import judge
    from tools.argonia_world.water import layer
    from tools.argonia_world.water import steps as stp
    if cw is None:
        return []
    cells_p, rec_p = water_out / "cells.jsonl", water_out / "records.json"
    if not cells_p.exists() or not index_path.exists():
        print(f"water check: no {cells_p} or {index_path}: placement rules skipped")
        return []
    resolver = pz.Resolver(pz.Index.load(index_path))
    kind_of = {resolver.resolve(m)[0].form_key: k for k, (m, _, _) in stp.PIECES.items()}
    lines = [json.loads(x) for x in cells_p.read_text().splitlines() if x]
    refs = [(kind_of.get(r["base"]), tuple(r["pos"]), math.degrees(r["rot"][2]) % 360) for d in lines for r in d["refs"]]
    levels = {k: v[0] for k, v in cw._cells.items()}
    g = np.load(ground_path, mmap_mode="r") if ground_path.exists() else None
    bad = [f"{'hovering' if 'hovering surface' in b else 'pieces'}: {b}" for b in judge.pieces(cw.steps(), levels, refs, g)]
    if g is None:
        print(f"water check: no {ground_path}: bed and hovering rules skipped")
    else:
        x0, y0 = su.PROVINCE_CELL_SW
        bad += [f"hovering: {b}" for b in judge.hovering(levels, cw.steps(), g, lambda x, y: x0 <= x < x0 + su.PROVINCE_CELLS and y0 <= y < y0 + su.PROVINCE_CELLS)]
    templates = {r["formKey"]: r.get("template") for r in json.loads(rec_p.read_text())["records"]} if rec_p.exists() else {}
    by_cell = {(d["x"], d["y"]): d.get("waterType") for d in lines}
    cells = [(r[0], r[1], r[2], r[3], by_cell.get((r[0], r[1]))) for r in w.query(
        "SELECT cx, cy, body_id, reach_id FROM cell_water")]
    bad += [f"still/flow: {b}" for b in judge.still_flow(cells, templates)]
    n = collections.Counter(b.split(":")[0] for b in bad)
    print(f"water check placement: {len(refs)} pieces on {sum(1 for s in cw.steps() if s.chain != 'closed')} steps; "
          f"reds {dict(n)}")
    return [f"{k}: {v} reds, first {[b for b in bad if b.startswith(k)][:3]}" for k, v in n.items()]


def cmd_emit(out: Path, index_path: Path, ground_path: Path) -> int:
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
    unresolved = sorted(k for k, r in resolved.items() if r.kind != "base" and any(k in c for c in stp.CHAINS.values()))
    widths = {(r[0], r[1]): r[2] for r in w.query(
        "SELECT c.cx, c.cy, r.width_m FROM cell_water c JOIN hydrology_reach r ON r.id = c.reach_id")}
    lines: dict[tuple[int, int], dict] = {}
    for r in w.query("SELECT cx, cy, level_m, water_type, body_id, reach_id FROM cell_water"):
        lines[(r[0], r[1])] = {"x": r[0], "y": r[1], "waterHeight": su.rounded(su.metres_to_units(r[2]), 2),
                               "waterType": layer.type_key(layer.cell_type(r[3], r[4], r[5])), "refs": []}
    import numpy as np
    from tools.argonia_world.water import judge
    g = np.load(ground_path, mmap_mode="r") if ground_path.exists() else None
    sample = None
    no_channel = []
    for s in cw.steps():
        if s.chain == "closed":
            continue
        width_m = widths.get((s.cx, s.cy)) or (s.cross_hi - s.cross_lo) * su.PROVINCE_SAMPLE_M
        if g is not None and judge.buried(s, width_m, g):  # the ground kept no channel: a closed bank, no chain
            no_channel.append(f"({s.cx},{s.cy}) {s.edge}")
            continue
        dx, dy = stp.OUT[s.edge]
        for p in stp.place(s, width_m):
            if resolved[p["kind"]].kind != "base":
                continue
            cell = (s.cx + dx, s.cy + dy) if p["kind"] in stp.AT_FOOT else (s.cx, s.cy)  # the cell it stands in
            line = lines.setdefault(cell, {"x": cell[0], "y": cell[1], "refs": []})
            line["refs"].append({"base": resolved[p["kind"]].form_key,
                                 "pos": [su.rounded(v, 2) for v in p["pos"]],
                                 "rot": [su.rounded(v, 6) for v in su.yaw_to_rot(p["yaw"])],
                                 "scale": su.rounded(p["scale"], 4)})
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
            "overSlot": over, "noChannel": no_channel}
    if sample is not None:  # a falls step for the world sample's river stop
        plan["sampleStep"] = {"cell": [sample.cx, sample.cy], "edge": sample.edge, "upperM": sample.upper_m,
                              "lowerM": sample.lower_m, "chain": sample.chain}
    (out / "plan.json").write_text(json.dumps(plan, indent=1) + "\n")
    print(f"water emit: {plan['cells']} cells, {plan['pieces']} piece refs, unresolved {unresolved}, "
          f"over slot {len(over)}, {len(no_channel)} steps with no channel in the ground (no chain): {no_channel[:12]}")
    return 1 if unresolved or over else 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="water", description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=["solve", "check", "emit", "records"])
    ap.add_argument("--out", default=str(ROOT / "out" / "water"))
    ap.add_argument("--ground", default=str(ROOT / "out" / "terrain" / "ground-f32.npy"))
    ap.add_argument("--index", default=str(ROOT / "out" / "pieces-index.json"))
    a = ap.parse_args(argv)
    if a.cmd == "records":
        from tools.argonia_world.water import layer
        print(json.dumps(layer.records(), indent=1, sort_keys=True))
        return 0
    if a.cmd == "solve":
        return cmd_solve()
    if a.cmd == "check":
        return cmd_check(Path(a.out), Path(a.index), Path(a.ground))
    return cmd_emit(Path(a.out), Path(a.index), Path(a.ground))


if __name__ == "__main__":
    sys.exit(main())
