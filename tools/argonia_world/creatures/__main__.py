"""The province's creatures (1.15 §g): the mods' creatures, Skyrim's encounter method, our rules.

    python3 -m tools.argonia_world.creatures inventory [--json out/creatures/inventory.json]
        every creature the pinned Black Marsh mods ship, and how each mod places its own (inventory.py)
    python3 -m tools.argonia_world.creatures seed [--inventory out/creatures/inventory.json]
        write roster.py's rows and the derived lists and zones into the world database (seed.py)
    python3 -m tools.argonia_world.creatures lists
        rewrite the lists (seed.derive_lists) and the bands' spawns per cell (roster.BANDS) from the database's
        rows alone, without the laid stack
    python3 -m tools.argonia_world.creatures check [--out out/creatures] [--cells x0,y0,x1,y1,...]
        plan the 1.15 sample (terrain/world.py SAMPLE_1_15, or --cells) and run the checks (checks.py);
        exit 1 on a red
    python3 -m tools.argonia_world.creatures build --out <dir> [--sample] [--veg <vegetation shards>]
        plan the gate's sample (terrain/world.py SAMPLE) or the province and write the splice's shards (records.py)
    python3 -m tools.argonia_world.creatures readback --out <dir> --esm <esm> --gen <ArgoniaGen>
        the spliced plugin read back through Mutagen: the creature refs per cell equal the planner's
    python3 -m tools.argonia_world.creatures plan-check [--journey tests/journeys/creatures-kinds.yaml]
        the kinds the province plan puts within two cells of each creatures-kinds stand (plan_check.py); exit 1
        when a stop has fewer than 4 expected, no spawn point within 90 m or a blocked eye line
    python3 -m tools.argonia_world.creatures journey | kinds
        regenerate tests/journeys/creature-spots.yaml (journey.py) or creatures-kinds.yaml (tools/journeys/gen.py):
        state checks, no stills (owner 19:05 #41), then `tools.journeys check` on it
The vanilla measurement is python3 -m tools.argonia_world.vanilla.creatures.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def _inventory(a) -> int:
    from tools.argonia_world.creatures import inventory
    from tools.argonia_world.vanilla import creatures as vc
    sk = vc.scan()
    r = inventory.run({f & 0xFFFFFF: v for f, v in sk.races.items()})
    Path(a.json).parent.mkdir(parents=True, exist_ok=True)
    Path(a.json).write_text(json.dumps(r, indent=1) + "\n")
    for k, v in r.items():
        print(k, v.get("new_creature_npcs"), "new creature NPC_,", v.get("achr_exterior"), "exterior refs")
    return 0


def _seed(a) -> int:
    from tools.argonia_world import db
    from tools.argonia_world.creatures import seed
    print(seed.seed(db.open(cache=False), json.loads(Path(a.inventory).read_text())))
    return 0


def _lists(a) -> int:
    from tools.argonia_world import db
    from tools.argonia_world.creatures import roster, seed
    w = db.open(cache=False)
    for r in w.query("SELECT * FROM danger_band_level"):
        w.upsert("danger_band_level", {**dict(r), "spawns_per_cell": roster.BANDS[r["band"]]})
    n = seed.derive_lists(w)
    w.save()
    print(f"creatures lists: {len(w.rows('creature_list'))} lists, {n} entries")
    return 0


def _check(a) -> int:
    from tools.argonia_world import db
    from tools.argonia_world.creatures import build, checks
    from tools.argonia_world.terrain.grid import Sources
    from tools.argonia_world.terrain.world import SAMPLE_1_15
    from tools.argonia_world.water import solve
    t0 = time.time()
    w = db.open()
    boxes = SAMPLE_1_15
    if a.cells:
        v = [int(x) for x in a.cells.split(",")]
        boxes = [tuple(v[i:i + 4]) for i in range(0, len(v), 4)]
    src, cw = Sources.load(), solve.load(w)
    cells = build.sample_cells(boxes)
    run = build.run(w, src, cw, cells, Path(a.out), veg=ROOT / "out" / "terrain" / "vegetation")
    res = {"classes": checks.classes(w), "lists": checks.lists(w),
           "density": checks.density(run, src, cw, cells, run["stems"]), "levels": checks.levels(w), "unlevelled": checks.unlevelled(w, run),
           **checks.refs(run, src, cw)}
    res["seconds"] = round(time.time() - t0, 1)
    (Path(a.out) / "checks.json").write_text(json.dumps(res, indent=1, default=str) + "\n")
    bad = [k for k, v in res.items() if isinstance(v, dict) and v.get("fail")]
    print("region classes (kinds with a why):", res["classes"]["kinds"])
    print("kinds in each class's lists:", res["lists"]["kinds"])
    print("spawn refs per 100 cells by terrain (vanilla):", {t: f"{v['per_100']} ({v['vanilla']}) in {v['cells']}"
                                                             for t, v in res["density"]["by_terrain"].items()})
    print(f"refs {res['habitat']['refs']} on their habitat; dens {res['dens']['dens']} with a predator beside; "
          f"lists {res['levels']['lists']} at their band's fixed level; no-spawn violations "
          f"{len(res['no_spawn']['fail'] or [])}")
    u = res["unlevelled"]
    print(f"unlevelled (0035): {u['entries']} list entries at level 1, {u['fixed_forms']} scaling mod forms as "
          f"{u['actors']} fixed copies, zones min = max")
    for k in bad:
        print(f"creatures check red: {k}: {res[k]['fail']}")
    print(f"creatures checks: {8 - len(bad)} green, {len(bad)} red ({res['seconds']} s)")
    return 1 if bad else 0


def _build(a) -> int:
    from tools.argonia_world import db
    from tools.argonia_world import skyrim_units as su
    from tools.argonia_world.creatures import build, records
    from tools.argonia_world.terrain.grid import Sources
    from tools.argonia_world.terrain.world import SAMPLE
    from tools.argonia_world.water import solve
    w = db.open()
    if a.sample:
        cells = build.sample_cells(SAMPLE)
    else:
        x0, y0 = su.PROVINCE_CELL_SW
        cells = [(x, y) for y in range(y0, y0 + su.PROVINCE_CELLS) for x in range(x0, x0 + su.PROVINCE_CELLS)]
    r = build.run(w, Sources.load(ground=Path(a.ground) if a.ground else None), solve.load(w), cells, None, log=lambda s: None, veg=Path(a.veg) if a.veg else None,
                  cache=Path(a.out))
    n = records.write_shards(r["refs"], Path(a.out), records.fixed_forms(w))
    print(f"creatures build: {n} refs in {len(cells)} cells ({r['summary']['seconds']} s)")
    return 0


def _readback(a) -> int:
    import subprocess
    from tools.argonia_world import skyrim_units as su
    from tools.argonia_world.creatures import records
    x0, y0 = su.PROVINCE_CELL_SW
    lo = records.ref_id(x0, y0, 0)
    hi = records.ref_id(x0 + su.PROVINCE_CELLS - 1, y0 + su.PROVINCE_CELLS - 1, records.REF_SLOT - 1)
    rb = Path(a.out) / "readback.jsonl"
    r = subprocess.run([a.gen, "vegcheck", "--in", a.esm, "--first", f"{lo:X}", "--last", f"{hi:X}", "--out", str(rb)],
                       capture_output=True, text=True, check=False)
    if r.returncode:
        print(f"creatures readback red: {(r.stdout + r.stderr)[-500:]}")
        return 1
    got = {(c["x"], c["y"]): c["n"] for c in map(json.loads, rb.read_text().splitlines())}
    want = {(c["x"], c["y"]): len(c["refs"]) for c in records.read_cells(Path(a.out))}
    bad = [f"({x},{y}): {got.get((x, y), 0)} read back, {want.get((x, y), 0)} planned"
           for x, y in sorted(set(got) | set(want)) if got.get((x, y), 0) != want.get((x, y), 0)]
    print(f"creatures readback: {sum(got.values())} refs read back in {len(got)} cells, "
          f"{sum(want.values())} planned in {len(want)}")
    for b in bad[:5]:
        print(f"creatures readback red: {b}")
    from tools.argonia_world import db
    from tools.argonia_world.creatures import levelled
    w = db.open()
    lv = levelled.check(Path(a.esm), {r["form_key"] for r in w.query("SELECT form_key FROM creature_form "
                                                                      "WHERE pc_level_mult")})
    print(f"creatures unlevelled (0035, the plugin's own records): {lv['records']}")
    for b in lv["fail"] or []:
        print(f"creatures unlevelled red: {b}")
    return 1 if bad or lv["fail"] else 0


def _plan_check(a) -> int:
    from tools.argonia_world import db
    from tools.argonia_world import skyrim_units as su
    from tools.argonia_world.creatures import build, plan_check
    from tools.argonia_world.terrain.grid import Sources
    from tools.argonia_world.water import solve
    from tools.journeys import Build
    w = db.open()
    g = sorted((ROOT / "out" / "terrain" / "build").glob("*/ground-f32.npy"), key=lambda p: p.stat().st_mtime)[-1]
    x0, y0 = su.PROVINCE_CELL_SW
    cells = [(x, y) for y in range(y0, y0 + su.PROVINCE_CELLS) for x in range(x0, x0 + su.PROVINCE_CELLS)]
    run = build.run(w, Sources.load(ground=g), solve.load(w), cells, None, log=lambda s: None,
                    veg=ROOT / "out" / "terrain" / "vegetation", cache=ROOT / "out" / "terrain" / "creatures")
    rows = plan_check.run(run["refs"], w, Build(), Path(a.journey).read_text())
    for r in rows:
        print(f"plan-check {r['class']}: {r['spawns']} spawn refs within two cells ({r['own_spawns']} of the class's own "
              f"lists), {r['possible']} kinds possible, {r['expected']} expected, P(>={plan_check.KINDS_N}) {r['p_ge']}; "
              f"{r['within_reach']} spawn points within {plan_check.REACH_M:.0f} m; eye line "
              f"{'clear' if r['clear'] else 'blocked'}{'; RED: ' + ', '.join(r['fail']) if r['fail'] else ''}")
    bad = [r for r in rows if r["fail"]] or (len(rows) < 3 and [None])
    print(f"plan-check: {len(rows) - len([r for r in rows if r['fail']])} of {len(rows)} stops green")
    return 1 if bad else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="creatures")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("inventory")
    p.add_argument("--json", default=str(ROOT / "out" / "creatures" / "inventory.json"))
    p = sub.add_parser("seed")
    p.add_argument("--inventory", default=str(ROOT / "out" / "creatures" / "inventory.json"))
    sub.add_parser("lists")
    p = sub.add_parser("check")
    p.add_argument("--out", default=str(ROOT / "out" / "creatures"))
    p.add_argument("--cells")
    p = sub.add_parser("build")
    p.add_argument("--out", required=True)
    p.add_argument("--sample", action="store_true")
    p.add_argument("--veg", help="the vegetation's shards: bush or open cover per spawn")
    p.add_argument("--ground", help="the ground-f32.npy to place on (a pipeline run's frozen copy)")
    p = sub.add_parser("plan-check")
    p.add_argument("--journey", default=str(ROOT / "tests" / "journeys" / "creatures-kinds.yaml"))
    sub.add_parser("journey")
    sub.add_parser("kinds")
    p = sub.add_parser("readback")
    p.add_argument("--out", required=True)
    p.add_argument("--esm", required=True)
    p.add_argument("--gen", required=True)
    a = ap.parse_args(argv)
    return {"inventory": _inventory, "seed": _seed, "lists": _lists, "check": _check, "build": _build,
            "readback": _readback, "plan-check": _plan_check,
            "journey": lambda a: _refresh("creature-spots"), "kinds": lambda a: _refresh("creatures-kinds")}[a.cmd](a)


def _refresh(name: str) -> int:
    from tools.journeys.__main__ import refresh
    return refresh({name})


if __name__ == "__main__":
    sys.exit(main())
