"""The province's creatures (1.15 §g): the mods' creatures, Skyrim's encounter method, our rules.

    python3 -m tools.argonia_world.creatures inventory [--json out/creatures/inventory.json]
        every creature the pinned Black Marsh mods ship, and how each mod places its own (inventory.py)
    python3 -m tools.argonia_world.creatures seed [--inventory out/creatures/inventory.json]
        write roster.py's rows and the derived lists and zones into the world database (seed.py)
    python3 -m tools.argonia_world.creatures check [--out out/creatures] [--cells x0,y0,x1,y1,...]
        plan the 1.15 sample (terrain/world.py SAMPLE_1_15, or --cells) and run the checks (checks.py);
        exit 1 on a red
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
    run = build.run(w, src, cw, build.sample_cells(boxes), Path(a.out))
    res = {"classes": checks.classes(w), "levels": checks.levels(w), **checks.refs(run, src, cw)}
    res["seconds"] = round(time.time() - t0, 1)
    (Path(a.out) / "checks.json").write_text(json.dumps(res, indent=1, default=str) + "\n")
    bad = [k for k, v in res.items() if isinstance(v, dict) and v.get("fail")]
    print("region classes (kinds with a why):", res["classes"]["kinds"])
    print(f"refs {res['habitat']['refs']} on their habitat; dens {res['dens']['dens']} with a predator beside; "
          f"lists {res['levels']['lists']} at their band's fixed level; no-spawn violations "
          f"{len(res['no_spawn']['fail'] or [])}")
    for k in bad:
        print(f"creatures check red: {k}: {res[k]['fail']}")
    print(f"creatures checks: {5 - len(bad)} green, {len(bad)} red ({res['seconds']} s)")
    return 1 if bad else 0


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
    a = ap.parse_args(argv)
    return {"inventory": _inventory, "seed": _seed, "check": _check}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
