"""The province's vegetation (2.W4 §a, our own placement from the region rules) and its L1 checks.

    python3 -m tools.argonia_world.vegetation build --out out/vegetation [--sample | --cells x0,y0,x1,y1]
                                                   [--water out/water/cells.jsonl] [--land <dir>] [--budget]
        place every province cell (or the gate's sample, terrain/world.py SAMPLE), write the shards and
        summary.json, then run the L1 checks against the LAND shards in --land (when given). --budget (whole
        province only): compute each region's keep and write the vegetation_region_budget rows.
        Exit 1 when a check fails.
    python3 -m tools.argonia_world.vegetation forms --bmv-nifs <list> [--lists-only]
        read the Black Marsh mods' TREE/FLOR/STAT from the laid stack into object_form (every Skyrim.esm form
        dropped; --bmv-nifs: BM&V's archive file list, `unrar lb` of the vault's Data1/Data2.rar), then build the
        region object lists (lists.py) and set BM&V's dependency keep list to the meshes they use.
        --lists-only: rebuild the lists from the object_form rows already in the world (no stack needed)
    python3 -m tools.argonia_world.vegetation rocks --nifs <dir>
        our own STAT forms for chosen BM&V rock meshes (rocks.py): object_form rows with each NIF's bounds (<dir>
        holds meshes/... unpacked from BM&V's archive), then the lists rebuilt as `forms --lists-only`
    python3 -m tools.argonia_world.vegetation booth --out <shards>
        write tests/journeys/rock-booth.yaml and tests/scenes/rock-booth.txt from six placed rocks (booth.py)
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


ROLES = {"mushroom": "mushrooms, small to giant: the deep marsh's strangeness (owner, 2026-11-01)",
         "aquatic": "lily pads, reeds, kelp and coral: plants standing in water"}
DEPS = ROOT / "data" / "dependencies.json"


def set_bmv_keep(paths: list[str]) -> int:
    """BM&V's dependency row: its keep list = the non-flora meshes it had plus the flora meshes the lists use."""
    deps = json.loads(DEPS.read_text(encoding="utf-8"))
    row = next(d for d in deps["mods"] if d.get("id") == "bmv")
    flora = ("meshes/landscape/", "meshes/trdata/", "meshes/vurt", "meshes/sheogorad/plants", "meshes/landscaping/")
    old = [k for k in row["keep"] if not k.startswith(flora) or k == "meshes/trdata/mushrooms/tr_oth_tallmush01.nif"
           or k == "meshes/landscape/trees/reedsmall2.nif"]
    row["keep"] = old + sorted(set(paths) - set(old))
    DEPS.write_text(json.dumps(deps, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return len(row["keep"])


def _forms(a) -> int:
    from tools.argonia_world import db
    from tools.argonia_world.vegetation import forms, lists
    w = db.open()
    for k, v in ROLES.items():
        if not w.get("object_role", k):
            w.insert("object_role", id=k, about=v)
    if not a.lists_only:
        if not a.bmv_nifs:
            print("vegetation forms: --bmv-nifs is required (or --lists-only)", file=sys.stderr)
            return 2
        nifs = set(Path(a.bmv_nifs).read_text(encoding="utf-8").split())
        n = forms.write(w, forms.inventory(resolver=forms.resolver()), nifs)
        for k, v in sorted(n.items()):
            print(f"object_form {k[0]:22} {k[1]:8} {v}")
    rep = lists.build(w)
    w.save()
    print(f"bmv keep list: {set_bmv_keep(lists.bmv_keep(w))} paths")
    for rid, c in sorted(rep.items()):
        print(f"{rid:44} " + " ".join(f"{m}={n}" for m, n in sorted(c.items())))
    return 0


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
    bo = sub.add_parser("booth")
    bo.add_argument("--out", default=str(ROOT / "out" / "vegetation"))
    ro = sub.add_parser("rocks")
    ro.add_argument("--nifs", required=True)
    fo = sub.add_parser("forms")
    fo.add_argument("--bmv-nifs")
    fo.add_argument("--lists-only", action="store_true")
    b.add_argument("--sample", action="store_true")
    b.add_argument("--cells")
    b.add_argument("--budget", action="store_true")
    a = p.parse_args(argv)
    if a.cmd == "booth":
        from tools.argonia_world import db
        from tools.argonia_world.vegetation import booth
        for d in booth.write(Path(a.out), db.open()):
            print(f"booth: {d['edid']} {d['fid']:06X} cell {d['cell']} tilt {d['tilt']:.3f} rad")
        return 0
    if a.cmd == "rocks":
        from tools.argonia_world import db
        from tools.argonia_world.vegetation import rocks
        w = db.open()
        print(f"rocks: {rocks.write(w, Path(a.nifs))} own STAT forms")
        w.save()
        a.lists_only, a.bmv_nifs = True, None
        return _forms(a)
    if a.cmd == "forms":
        return _forms(a)
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
