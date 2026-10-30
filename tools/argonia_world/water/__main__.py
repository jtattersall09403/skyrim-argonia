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

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
REGRADE_PASSES = 2


def plan_province(log=print):
    """The designed plan of the whole province: (graph, reach rules, steps, field, design, turned tiles, cells, the
    ground it stands on, the regrade's floors and beds)."""
    from tools.argonia_world.water import classify, design, field, model, oriented, plan, steps

    t0 = time.time()
    g = model.load()
    rules = classify.classify(g)
    by_id = {r.id: (r.rule, r.water) for rs in rules.values() for r in rs}
    reach_rule = {r.id: r.rule for r in rules["reaches"]}
    wtypes = {rid: w for rid, (_, w) in by_id.items()}
    st, _ = steps.plan(g, reach_rule)
    inp = field.Inputs.load()
    raw = inp.ground
    # the whole plan stands on the ground as the LAND stores it (quantised and limited), not the refined field
    inp.ground = game_ground(raw, {})
    # the step-and-pool regrade: the beds carved first, then the design on the carved ground and the banks and
    # sills its tiles ask for
    beds = oriented.carve(g, st, inp.ground)
    inp.ground = game_ground(raw, {}, {i: v[0] for i, v in beds.items()})
    floors: dict = {}
    for _ in range(REGRADE_PASSES):  # the banks a tile asks for change the field the next tiles stand on
        f = field.build(g, inp, by_id, st)
        design.design(g, f, inp.ground)
        plan.shown_levels(f)
        oriented.plan(g, st, f, inp.ground, wtypes, plan.LEAK_TOL_M, floors)
        clamped = oriented.clamp_beds(beds, f)
        del f
        inp.ground = game_ground(raw, {i: v[0] for i, v in floors.items()}, {i: v[0] for i, v in beds.items()})
        log(f"water plan: regrade {len(beds)} beds ({clamped} clamped to adjoining lower water), {len(floors)} banks and sills ({time.time() - t0:.0f} s)")
    # the design and the plan on the regraded ground (the LAND's own)
    ground = inp.ground
    f = field.build(g, inp, by_id, st)
    des = design.design(g, f, ground)
    plan.shown_levels(f)
    oplanes = oriented.plan(g, st, f, ground, wtypes, plan.LEAK_TOL_M)
    cells = plan.plan_cells(f, ground, oplanes, greedy_over=0)
    return g, reach_rule, st, f, des, oplanes, cells, ground, floors, beds


def run_plan(out: Path, index_path: Path, write_db: bool = False) -> int:
    from tools.argonia_world import pieces as pz
    from tools.argonia_world import skyrim_units as su
    from tools.argonia_world.water import budget, classify, design, field, layer, plan, steps

    t0 = time.time()
    g, reach_rule, st, f, des, oplanes, cells, ground, floors, beds = plan_province()
    rules = classify.classify(g)
    n = ground.shape[0]
    pieces = steps.pieces(g, reach_rule, st)
    # the pieces into their cells
    for p in pieces:
        x, y = int(p.east_m / field.MPP), int(p.south_m / field.MPP)
        cx, cy = plan.cell_index(min(x, n - 1), min(y, n - 1), (n - 1) // plan.Q)
        cells.setdefault((cx, cy), plan.CellPlan(cx, cy, "default")).pieces.append(p)
    R = plan.realised(f, cells, n)
    checks = {
        "bodies": plan.check_bodies(g, f, R, ground, des),
        "wet": plan.check_wet(f, R, ground),
        "overlap": plan.check_overlap(cells, n),
        "float": plan.check_float(f, cells, ground),
        "walls": plan.check_walls(f, ground, pieces),
        "sides": plan.check_sides(f, ground, pieces),
        "steps": plan.check_steps(g, st),
        "banks": plan.check_banks(g, st, ground, f.level),
        "groundAs": "build.game_heights_m with the step-and-pool regrade (the LAND's own ground)",
    }
    # the pieces resolved through the piece index (vanilla kit, old 0064)
    try:
        resolver = pz.Resolver(pz.Index.load(index_path))
        resolved = {k: resolver.resolve(m)[0] for k, (m, _, _) in steps.PIECES.items()}
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
    over_budget = budget.over(cells)
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
    (out / "records.json").write_text(json.dumps({"schema": 1, "records": layer.records()}, indent=1,
                                                 sort_keys=True) + "\n", encoding="utf-8")
    tables = {**design.rows(des), "water_regrade": regrade_rows(floors, beds, n)}
    totals = design_totals(des, floors, beds, tables)
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
                  "overSlot": over, "overBudget": over_budget},
        "design": totals,
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
    if b["uncovered"]:
        fails.append(f"bodies: {len(b['uncovered'])} kept bodies not realised, first {b['uncovered'][:5]}")
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
    if over_budget:
        fails.append(f"cells over the plane budget {budget.BUDGET} (the design must change, nothing falls back): "
                     f"{len(over_budget)}: {over_budget[:10]}")
    if write_db:
        write_tables(tables)
        print(f"water plan: world db: {', '.join(f'{t} {len(r)}' for t, r in tables.items())} rows")
    elif (stale := stale_tables(tables)):
        fails.append(f"the world db's water design rows differ from the plan in {stale}: run "
                     "`python -m tools.argonia_world.water plan --write-db` and commit the db rows")
    print(f"water plan: {b['realised']} bodies realised, {b['droppedByDesign']} dropped by design, "
          f"{len(b['uncovered'])} uncovered; {len(cells)} cells with water ({dict(modes)}); {nplanes} plane refs "
          f"(max {summary['cells']['planesMaxPerCell']}, p95 {summary['cells']['planesP95PerCell']} per cell); "
          f"{summary['steps']['steps']} steps on {len(st)} reaches; pieces {summary['steps']['pieces']}; "
          f"{totals['basinsKept']} basins kept, {totals['basinsDropped']} dropped; {totals['regradedVertices']} regraded vertices; "
          f"walls {checks['walls']['samples']}; open sides {checks['sides']['samples']} "
          f"(reach {checks['sides']['bySource']['reach']}); banks flagged on {len(checks['banks']['flagged'])} reaches; "
          f"sample reach {sample}; {summary['seconds']} s -> {out}")
    for x in fails:
        print("FAIL", x)
    return 1 if fails else 0


def game_ground(ground, floors: dict, ceilings: dict | None = None):
    """The province's ground as the LAND will store it (terrain build.game_heights_m: quantised and limited, the
    regrade applied), in row bands; the frozen array where the terrain grid is not there."""
    from tools.argonia_world.terrain import build, grid
    try:
        src = grid.Sources.load()
    except (FileNotFoundError, OSError) as e:
        print(f"water plan: no terrain grid ({e}); float and banks use the refined heightfield")
        return ground
    src.regrade = regrade_from(floors, ground.shape[0], src.pad, ceilings)
    n = ground.shape[0]
    out = np.empty((n, n), dtype=np.float32)
    band = 256
    for r0 in range(0, n, band):
        r1 = min(n, r0 + band)
        out[r0:r1] = build.game_heights_m(src, src.pad + r0, src.pad + r1, src.pad, src.pad + n)
    return out


def regrade_from(floors: dict, n: int, pad: int, ceilings: dict | None = None):
    from tools.argonia_world.terrain import water_regrade
    return water_regrade.Regrade.from_flat(floors, n, pad, ceilings)


def regrade_rows(floors: dict, beds: dict, n: int) -> list[dict]:
    """The step-and-pool regrade's vertices for the world db's `water_regrade`."""
    out = []
    for i in sorted(beds):
        y, x = divmod(i, n)
        out.append({"x": x, "y": y, "kind": "bed", "z_m": beds[i][0], "entity_id": beds[i][1]})
    for i in sorted(floors):
        y, x = divmod(i, n)
        z, rid, kind = floors[i]
        out.append({"x": x, "y": y, "kind": kind, "z_m": z, "entity_id": rid})
    return out


def design_totals(des, floors: dict, beds: dict, tables: dict) -> dict:
    kept = [b for b in des.basins if b.outcome == "kept"]
    dropped = [b for b in des.basins if b.outcome == "dropped"]
    reasons = collections.Counter(b.reason.split(":")[0] for b in dropped)
    return {"basinsKept": len(kept), "basinsDropped": len(dropped), "droppedBasinsByReason": dict(reasons),
            "droppedAreaM2": round(sum(b.area_m2 for b in dropped)),
            "keptAreaM2": round(sum(b.area_m2 for b in kept)),
            "basinLevelRules": dict(collections.Counter(b.level_rule for b in kept)),
            "basinsSpilled": des.spilled, "driedToMarshSamples": des.dried, "shoreGrownSamples": des.grown,
            "droppedSamples": des.dropped_samples,
            "bodyOutcomes": dict(collections.Counter(v[0] for v in des.body.values())),
            "regradedVertices": len(floors) + len(beds),
            "regradeByKind": {"bed": len(beds), **collections.Counter(v[2] for v in floors.values())},
            "rows": {t: len(r) for t, r in tables.items()}}


def write_tables(tables: dict) -> None:
    """Replace the budget's tables' rows through db.py."""
    from tools.argonia_world import db
    w = db.open()
    for t, rows in tables.items():
        pk = w.table(t).pk
        for r in w.query(f'SELECT {", ".join(chr(34) + k + chr(34) for k in pk)} FROM "{t}"'):
            w.delete(t, *tuple(r))
        w.insert_many(t, rows)
    w.save(list(tables))


def stale_tables(tables: dict) -> list[str]:
    from tools.argonia_world import db
    w = db.open()
    bad = []
    for t, rows in tables.items():
        have = [dict(r) for r in w.query(f'SELECT * FROM "{t}"')]
        cols = list(rows[0]) if rows else []
        key = lambda r: tuple(str(r[c]) for c in cols)  # noqa: E731
        if len(have) != len(rows) or sorted(map(key, have)) != sorted(map(key, rows)):
            bad.append(t)
    return bad


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="water", description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=["plan", "records"])
    ap.add_argument("--out", default=str(ROOT / "out" / "water"))
    ap.add_argument("--index", default=str(ROOT / "out" / "pieces-index.json"))
    ap.add_argument("--write-db", action="store_true", help="write the design's basin, body and regrade rows")
    a = ap.parse_args(argv)
    if a.cmd == "records":
        from tools.argonia_world.water import layer
        print(json.dumps(layer.records(), indent=1, sort_keys=True))
        return 0
    return run_plan(Path(a.out), Path(a.index), a.write_db)


if __name__ == "__main__":
    sys.exit(main())
