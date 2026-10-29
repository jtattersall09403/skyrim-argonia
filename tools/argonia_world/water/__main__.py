"""The water plan and its L1 checks (2.W2).

    python3 -m tools.argonia_world.water plan [--out out/water] [--index out/pieces-index.json]
        classify every body, reach and spring; step the rivers; build the water-level field; plan each cell
        (default / height / planes) and the step pieces; run the L1 checks; write plan.json (summary, classes,
        checks, the sample reach) and cells.jsonl (the per-cell stream WaterRecords.ApplyCell reads).
        Exit 1 when a check fails.
    python3 -m tools.argonia_world.water records    the WATR and ACTI intermediate records as JSON

Reads the graph through db.py and the frozen arrays in $ARGONIA_DATA (memory-mapped where they are .npy).
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def run_plan(out: Path, index_path: Path) -> int:
    from tools.argonia_world import pieces as pz
    from tools.argonia_world import skyrim_units as su
    from tools.argonia_world.water import classify, field, layer, model, oriented, plan, steps

    t0 = time.time()
    g = model.load()
    rules = classify.classify(g)
    by_id = {r.id: (r.rule, r.water) for rs in rules.values() for r in rs}
    reach_rule = {r.id: r.rule for r in rules["reaches"]}
    st, pieces = steps.plan(g, reach_rule)
    inp = field.Inputs.load()
    f = field.build(g, inp, by_id, st)
    n = inp.ground.shape[0]
    plan.shown_levels(f, n)
    oplanes = oriented.plan(g, st, f, inp.ground, {rid: w for rid, (_, w) in by_id.items()}, plan.LEAK_TOL_M)
    cells = plan.plan_cells(f, inp.ground, oplanes)
    # the pieces into their cells
    for p in pieces:
        x, y = int(p.east_m / field.MPP), int(p.south_m / field.MPP)
        cx, cy = plan.cell_index(min(x, n - 1), min(y, n - 1), (n - 1) // plan.Q)
        cells.setdefault((cx, cy), plan.CellPlan(cx, cy, "default")).pieces.append(p)
    R = plan.realised(f, cells, n)
    checks = {
        "bodies": plan.check_bodies(g, f, R, inp.ground),
        "wet": plan.check_wet(f, R, inp.ground),
        "overlap": plan.check_overlap(cells, n),
        "float": plan.check_float(f, cells, inp.ground),
        "steps": plan.check_steps(g, st),
        "banks": plan.check_banks(g, st, inp.ground, f.level),
    }
    # the pieces resolved through the piece index (vanilla kit, old 0064)
    try:
        res = pz.Resolver(pz.Index.load(index_path))
        resolved = {k: res.resolve(m)[0] for k, (m, _, _) in steps.PIECES.items()}
        checks["pieces"] = {k: {"kind": r.kind, "formKey": r.form_key, "edid": r.edid} for k, r in resolved.items()}
        unresolved = [k for k, r in resolved.items() if r.kind != "base"]
    except FileNotFoundError as e:
        resolved, unresolved = {}, list(steps.PIECES)
        checks["pieces"] = {"error": str(e)}
    sample = plan.sample_reach(g, st)
    sr = g.reaches[sample]
    sample_pieces = [p for p in pieces if p.reach == sample]
    out.mkdir(parents=True, exist_ok=True)
    # cells.jsonl: one line per cell with water work, refs in Skyrim units with their FormKeys
    lines, over = [], []
    nplanes = 0
    for (cx, cy), cp in sorted(cells.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        refs = []
        for op in cp.oplanes:
            x, y = su.province_to_skyrim(op.east_m, op.south_m)
            refs.append({"base": layer.plane_key(op.wtype),
                         "pos": [su.rounded(x, 2), su.rounded(y, 2), su.rounded(su.metres_to_units(op.level_m), 2)],
                         "rot": [su.rounded(v, 6) for v in su.yaw_to_rot(op.yaw_deg)],
                         "scale": su.rounded(su.metres_to_units(op.side_m) / plan.PLANE_MESH_UNITS, 6)})
        for p in cp.planes:
            for r in plan.plane_refs(p):
                refs.append({"base": layer.plane_key(p.wtype), **r})
        nplanes += len(refs)
        for p in cp.pieces:
            if p.kind not in resolved or resolved[p.kind].kind != "base":
                continue
            _, w_units, h_units = steps.PIECES[p.kind]
            size = su.metres_to_units(p.drop_m) / h_units if p.kind in ("falls", "mist") else \
                su.metres_to_units(p.width_m) / w_units
            x, y = su.province_to_skyrim(p.east_m, p.south_m)
            refs.append({"base": resolved[p.kind].form_key,
                         "pos": [su.rounded(x, 2), su.rounded(y, 2), su.rounded(su.metres_to_units(p.z_m), 2)],
                         "rot": [su.rounded(v, 6) for v in su.yaw_to_rot(p.yaw_deg)],
                         "scale": su.rounded(min(10.0, max(0.1, size)), 4)})
        if len(refs) > layer.REFS_PER_CELL:
            over.append(f"({cx},{cy}): {len(refs)} refs")
            refs = refs[:layer.REFS_PER_CELL]
        for k, r in enumerate(refs):
            r["formKey"] = layer.ref_key(cx, cy, k)
        line = {"x": cx, "y": cy, "refs": refs}
        if cp.mode == "height":
            line["waterHeight"] = su.rounded(su.metres_to_units(cp.level_m), 2)
            line["waterType"] = layer.type_key(cp.wtype)
        lines.append(json.dumps(line, sort_keys=True, separators=(",", ":")))
    (out / "cells.jsonl").write_text("".join(x + "\n" for x in lines), encoding="utf-8")
    modes = collections.Counter(cp.mode for cp in cells.values())
    per_cell = sorted((sum(len(plan.squares(p)) for p in cp.planes) + len(cp.oplanes) for cp in cells.values()),
                      reverse=True)
    summary = {
        "classes": {k: dict(collections.Counter(r.cls for r in v)) for k, v in rules.items()},
        "rules": {k: dict(collections.Counter(r.rule for r in v)) for k, v in rules.items()},
        "waterTypes": {k: dict(collections.Counter(r.water for r in v)) for k, v in rules.items()},
        "field": {"flooded": f.flooded, "empty": f.empty,
                  "sources": {s: int((f.source == i).sum()) for i, s in
                              enumerate(["dry", "body", "raster-rest", "sea", "reach", "shore", "hollow"])},
                  "shoreFilled": f.shore_filled},
        "cells": {"withWater": len(cells), "modes": dict(modes), "turnedStepPlanes": len(oplanes),
                  "planeRefs": nplanes, "planesMaxPerCell": per_cell[0] if per_cell else 0,
                  "planesP95PerCell": per_cell[len(per_cell) // 20] if per_cell else 0,
                  "planeSides": dict(collections.Counter(str(s) for cp in cells.values() for p in cp.planes
                                                         for _, _, s in plan.squares(p))),
                  "overSlot": over},
        "steps": {"reaches": len(st), "steps": sum(len(v) for v in st.values()),
                  "pieces": dict(collections.Counter(p.kind for p in pieces))},
        "sampleReach": {"id": sample, "kind": sr.kind, "river": sr.river, "lengthM": sr.length_m,
                        "dropM": round(sr.level_from_m - sr.level_to_m, 3), "widthM": sr.width_m,
                        "steps": [{"index": s.index, "fromM": round(s.s0, 2), "toM": round(s.s1, 2),
                                   "levelM": round(s.level_m, 3)} for s in st[sample]],
                        "pieces": [{"kind": p.kind, "eastM": round(p.east_m, 2), "southM": round(p.south_m, 2),
                                    "zM": round(p.z_m, 3), "dropM": round(p.drop_m, 3), "yawDeg": round(p.yaw_deg, 1)}
                                   for p in sample_pieces],
                        "start": dict(zip(("eastM", "southM"), sr.points[0])),
                        "skyrimStart": list(su.province_to_skyrim(*sr.points[0])),
                        "banks": checks["banks"]["flagged"].get(sample)},
        "checks": checks,
        "records": layer.records(),
        "seconds": round(time.time() - t0, 1),
    }
    (out / "plan.json").write_text(json.dumps(summary, indent=1, sort_keys=True, default=str) + "\n", encoding="utf-8")
    fails = []
    b = checks["bodies"]
    if b["covered"] != b["bodies"]:
        fails.append(f"bodies: {b['covered']}/{b['bodies']} have a placed water record or a cell water height")
    if checks["wet"]["unrealised"]:
        fails.append(f"wet: {checks['wet']['unrealised']} wet samples have no water over them")
    ov = checks["overlap"]
    if ov["sameHeightOverlapSamples"] or ov["planesAtCellLevel"]:
        fails.append(f"overlap: {ov}")
    if checks["float"]["floatingSamples"]:
        fails.append(f"float: {checks['float']}")
    if checks["steps"]["violations"]:
        fails.append(f"steps: {len(checks['steps']['violations'])} violations")
    if unresolved:
        fails.append(f"pieces unresolved: {unresolved}")
    if over:
        fails.append(f"cells over their FormID slot: {len(over)}")
    print(f"water plan: {b['covered']}/{b['bodies']} bodies covered; {len(cells)} cells with water "
          f"({dict(modes)}); {nplanes} plane refs; {summary['steps']['steps']} steps on {len(st)} reaches; "
          f"pieces {summary['steps']['pieces']}; banks flagged on {len(checks['banks']['flagged'])} reaches; "
          f"sample reach {sample}; {summary['seconds']} s -> {out}")
    for x in fails:
        print("FAIL", x)
    return 1 if fails else 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="water", description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=["plan", "records"])
    ap.add_argument("--out", default=str(ROOT / "out" / "water"))
    ap.add_argument("--index", default=str(ROOT / "out" / "pieces-index.json"))
    a = ap.parse_args(argv)
    if a.cmd == "records":
        from tools.argonia_world.water import layer
        print(json.dumps(layer.records(), indent=1, sort_keys=True))
        return 0
    return run_plan(Path(a.out), Path(a.index))


if __name__ == "__main__":
    sys.exit(main())
