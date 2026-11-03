"""python3 -m tools.journeys refresh [--only a,b]   re-derive every data-driven journey from the current build, pull
                                                  each vantage out of water and foliage; exit 1 if any is still stale
   python3 -m tools.journeys check                 the L1 check alone: every stand against the current build
   python3 -m tools.journeys ledger pass <journey> <step>   record a reader's PASS for the step's last run in the
                                                  pass ledger (tools/pass_ledger.py): it is not run again on the
                                                  same inputs

The build: out/terrain (the LAND heights, the vegetation shards), out/water/cells.jsonl, the world DB (db.py).
"""
from __future__ import annotations

import json
import math
import re
import sys

from tools.argonia_world import skyrim_units as su
from tools.journeys import DERIVED, JOURNEYS, ROOT, SUBJECT_M, Build, check, eye_of, frame, reframe, stand_near
from tools.journeys import gen


def _panel(b: Build, w, log: list) -> None:
    from tools.argonia_world import panel
    vs = panel.vantages(w)
    for v in vs:
        x, y = v["pos"][0], v["pos"][1]
        ex, ey, ez = eye_of(b, x, y)
        a = math.radians(v["yaw_deg"])
        d = SUBJECT_M * su.UNITS_PER_METRE
        f = frame(b, x, y, (ex + math.sin(a) * d, ey + math.cos(a) * d, ez))
        if not f["clear"]:   # the approach line found none: any dry, standable stand round it with a clear ray
            near = stand_near(b, x, y, v["yaw_deg"])
            if near:
                f = {**f, "x": near["x"], "y": near["y"], "moved_m": near["moved_m"], "clear": True,
                     "why": f["why"] + "; ray, plants or slope"}
        log.append({"journey": "world-panel", "step": v["id"], "moved_m": f["moved_m"], "why": f["why"], "clear": f["clear"]})
        if f["moved_m"]:
            v["x_m"], v["y_m"] = (round(c, 2) for c in su.skyrim_to_province(f["x"], f["y"]))
        g = su.units_to_metres(b.ground_u(f["x"], f["y"]))  # the game's ground (LAND), not the generator's
        v["ground_m"] = round(g, 2)
        v["pos"] = [round(f["x"]), round(f["y"]), round((g + panel.EYE_M) * su.UNITS_PER_METRE)]
    panel.sync_markers(w, vs, True)
    panel.SCENE.write_bytes(panel.scene_text(vs).encode())
    panel.JOURNEY.write_text(panel.journey_text(vs))


def _reframe(b: Build, name: str, log: list) -> None:
    p = JOURNEYS / f"{name}.yaml"
    steps: list = []
    p.write_text(reframe(b, p.read_text(), steps))
    log += [{"journey": name, **s} for s in steps]


def refresh(only: set[str] | None = None) -> int:
    from tools.argonia_world import db
    from pathlib import Path
    want = lambda n: only is None or n in only  # noqa: E731
    b, w, log = Build(), db.open(), []
    reach = _reach_lines()  # the generators write whole files: each journey's `reach:` line is put back after
    veg = ROOT / "out" / "terrain" / "vegetation"
    if want("world-panel"):
        _panel(b, w, log)
    if want("creature-spots"):
        from tools.argonia_world.creatures import journey as cj
        cj.write(ROOT / "out" / "creatures")
        _reframe(b, "creature-spots", log)
    if want("tree-seat"):
        from tools.argonia_world.vegetation import tree_booth
        tree_booth.write(Path(veg), w)
        _reframe(b, "tree-seat", log)
    if want("rock-booth"):
        from tools.argonia_world.vegetation import booth
        booth.write(Path(veg), w)
        _reframe(b, "rock-booth", log)
    if want("river-steps"):
        (JOURNEYS / "river-steps.yaml").write_text(gen.river_steps(b, w, log))
    if want("water-types"):
        (JOURNEYS / "water-types.yaml").write_text(gen.water_types(b, w, log))
    if want("road-look"):
        (JOURNEYS / "road-look.yaml").write_text(gen.road_look(b, w, log))
    if want("creatures-kinds"):
        (JOURNEYS / "creatures-kinds.yaml").write_text(gen.creatures_kinds(b, w, log))
    for n in ("claywater-look", "claywater-walk"):
        if want(n):
            (JOURNEYS / n).with_suffix(".yaml").write_text(gen.claywater(b, n, log))
    moved = [r for r in log if r["moved_m"]]
    stuck = [r for r in log if not r["clear"]]
    for r in moved + [r for r in stuck if r not in moved]:
        print(f"journeys: {r['journey']} {r['step']}: {r['why']}; moved {r['moved_m']} m"
              f"{'' if r['clear'] else ' (no clear stand within reach)'}")
    _put_reach(reach)
    (ROOT / "out" / "journeys-refresh.json").write_text(json.dumps(log, indent=1))
    print(f"journeys refresh: {len(log)} vantages, {len(moved)} moved, {len(stuck)} not clear")
    return _check(b, only)


def _reach_lines() -> dict:
    """Each journey file's `reach:` line (the pass ledger's inputs, tools/pass_ledger.py)."""
    out = {}
    for f in JOURNEYS.glob("*.yaml"):
        m = re.search(r"^reach:.*\n", f.read_text(), re.M)
        if m:
            out[f] = m.group(0)
    return out


def _put_reach(lines: dict) -> None:
    """A regenerated journey that lost its `reach:` line gets it back, after its `id:` line."""
    for f, line in lines.items():
        t = f.read_text() if f.exists() else ""
        if re.search(r"^reach:", t, re.M):
            continue
        m = re.search(r"^id: .*\n", t, re.M)
        if m:
            f.write_text(t[:m.end()] + line + t[m.end():])


def _check(b: Build, only=None) -> int:
    bad = {n: e for n, e in check(b, [n for n in DERIVED if only is None or n in only]).items() if e}
    for n, es in bad.items():
        for e in es:
            print(f"journeys STALE {n}: {e}")
    print(f"journeys check: {sum(map(len, bad.values()))} stale stands in {len(bad)} journeys")
    return 1 if bad else 0


def main(argv: list[str]) -> int:
    only = None
    if "--only" in argv:
        only = set(argv[argv.index("--only") + 1].split(","))
    if argv[:1] == ["refresh"]:
        return refresh(only)
    if argv[:2] == ["ledger", "pass"] and len(argv) == 4:
        from tools import pass_ledger
        row = pass_ledger.reader_pass(argv[2], argv[3])
        print(f"ledger: {argv[2]} {argv[3]} PASS (reader) on {row['reach_hash']}, run {row.get('run')}")
        return 0
    if argv[:1] == ["check"]:
        return _check(Build(), only)
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
