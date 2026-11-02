"""The province's creatures (1.15 §g): the mods' creatures, Skyrim's encounter method, our rules.

    python3 -m tools.argonia_world.creatures inventory [--json out/creatures/inventory.json]
        every creature the pinned Black Marsh mods ship, and how each mod places its own (inventory.py)
    python3 -m tools.argonia_world.creatures seed [--inventory out/creatures/inventory.json]
        write roster.py's rows and the derived lists and zones into the world database (seed.py)
    python3 -m tools.argonia_world.creatures check [--out out/creatures] [--cells x0,y0,x1,y1,...]
        plan the 1.15 sample (terrain/world.py SAMPLE_1_15, or --cells) and run the checks (checks.py);
        exit 1 on a red
    python3 -m tools.argonia_world.creatures build --out <dir> [--sample] [--veg <vegetation shards>]
        plan the gate's sample (terrain/world.py SAMPLE) or the province and write the splice's shards (records.py)
    python3 -m tools.argonia_world.creatures readback --out <dir> --esm <esm> --gen <ArgoniaGen>
        the spliced plugin read back through Mutagen: the creature refs per cell equal the planner's
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
    run = build.run(w, src, cw, build.sample_cells(boxes), Path(a.out), veg=ROOT / "out" / "terrain" / "vegetation")
    res = {"classes": checks.classes(w), "levels": checks.levels(w), "unlevelled": checks.unlevelled(w, run),
           **checks.refs(run, src, cw)}
    res["seconds"] = round(time.time() - t0, 1)
    (Path(a.out) / "checks.json").write_text(json.dumps(res, indent=1, default=str) + "\n")
    bad = [k for k, v in res.items() if isinstance(v, dict) and v.get("fail")]
    print("region classes (kinds with a why):", res["classes"]["kinds"])
    print(f"refs {res['habitat']['refs']} on their habitat; dens {res['dens']['dens']} with a predator beside; "
          f"lists {res['levels']['lists']} at their band's fixed level; no-spawn violations "
          f"{len(res['no_spawn']['fail'] or [])}")
    u = res["unlevelled"]
    print(f"unlevelled (0035): {u['entries']} list entries at level 1, {u['fixed_forms']} scaling mod forms as "
          f"{u['actors']} fixed copies, zones min = max")
    for k in bad:
        print(f"creatures check red: {k}: {res[k]['fail']}")
    print(f"creatures checks: {6 - len(bad)} green, {len(bad)} red ({res['seconds']} s)")
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


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="creatures")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("inventory")
    p.add_argument("--json", default=str(ROOT / "out" / "creatures" / "inventory.json"))
    p = sub.add_parser("seed")
    p.add_argument("--inventory", default=str(ROOT / "out" / "creatures" / "inventory.json"))
    p = sub.add_parser("check")
    p.add_argument("--out", default=str(ROOT / "out" / "creatures"))
    p.add_argument("--cells")
    p = sub.add_parser("build")
    p.add_argument("--out", required=True)
    p.add_argument("--sample", action="store_true")
    p.add_argument("--veg", help="the vegetation's shards: bush or open cover per spawn")
    p.add_argument("--ground", help="the ground-f32.npy to place on (a pipeline run's frozen copy)")
    p = sub.add_parser("readback")
    p.add_argument("--out", required=True)
    p.add_argument("--esm", required=True)
    p.add_argument("--gen", required=True)
    a = ap.parse_args(argv)
    return {"inventory": _inventory, "seed": _seed, "check": _check, "build": _build,
            "readback": _readback}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
