"""The province's vegetation (2.W4 §a, our own placement from the region rules) and its L1 checks.

    python3 -m tools.argonia_world.vegetation build --out out/vegetation [--sample | --cells x0,y0,x1,y1]
                                                   [--water out/water/cells.jsonl] [--land <dir>] [--budget]
        place every province cell (or the gate's sample, terrain/world.py SAMPLE), write the shards and
        summary.json, then run the L1 checks against the LAND shards in --land (when given). --budget (whole
        province only): compute each region's keep and write the vegetation_region_budget rows.
        Exit 1 when a check fails.
    python3 -m tools.argonia_world.vegetation check --out out/vegetation --land <dir> [--water ...]
    python3 -m tools.argonia_world.vegetation readback --out out/vegetation --esm <ArgoniaWorld.esm> --gen <ArgoniaGen>
        the spliced plugin read back through Mutagen: ref counts per cell equal the shards'; prints its sha256
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
WATER = ROOT / "out" / "water" / "cells.jsonl"


def _boxes(a) -> list | None:
    if a.sample:
        from tools.argonia_world.terrain.world import SAMPLE
        return [tuple(b) for b in SAMPLE]
    if a.cells:
        v = [int(x) for x in a.cells.split(",")]
        return [tuple(v[i:i + 4]) for i in range(0, len(v), 4)]
    return None


def _check(a) -> int:
    from tools.argonia_world.vegetation import checks
    res = checks.run(Path(a.out), Path(a.land), Path(a.water), log=print)
    (Path(a.out) / "checks.json").write_text(json.dumps(res, indent=1, sort_keys=True) + "\n")
    bad = [k for k, v in res.items() if isinstance(v, dict) and v.get("fail")]
    for k in bad:
        print(f"vegetation check red: {k}: {res[k]['fail']}")
    print(f"vegetation checks: {len(res) - len(bad)} green, {len(bad)} red ({res['refs']} refs)")
    return 1 if bad else 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="vegetation")
    sub = p.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    for q in (b, sub.add_parser("check")):
        q.add_argument("--out", default=str(ROOT / "out" / "vegetation"))
        q.add_argument("--water", default=str(WATER))
        q.add_argument("--land")
    rb = sub.add_parser("readback")
    rb.add_argument("--out", default=str(ROOT / "out" / "vegetation"))
    rb.add_argument("--esm", required=True)
    rb.add_argument("--gen", required=True)
    b.add_argument("--sample", action="store_true")
    b.add_argument("--cells")
    b.add_argument("--budget", action="store_true")
    a = p.parse_args(argv)
    if a.cmd == "readback":
        from tools.argonia_world.vegetation import checks
        res = checks.readback(Path(a.out), Path(a.esm), Path(a.gen))
        print(f"vegetation readback: {json.dumps(res)}")
        return 1 if res.get("fail") else 0
    if a.cmd == "build":
        from tools.argonia_world.vegetation import build
        boxes = _boxes(a)
        if a.budget and boxes:
            print("vegetation: --budget needs the whole province", file=sys.stderr)
            return 2
        t0 = time.time()
        s = build.run(Path(a.out), Path(a.water), cells=boxes, budget=a.budget, log=print)
        pr = s["province"]
        print(f"vegetation: {pr['refs']} refs in {pr['cells']} cells (max {pr['max']}, p95 {pr['p95']:.0f}) "
              f"in {time.time() - t0:.0f} s")
        if not a.land:
            return 0
    if not a.land:
        print("vegetation check: --land is required", file=sys.stderr)
        return 2
    return _check(a)


if __name__ == "__main__":
    sys.exit(main())
