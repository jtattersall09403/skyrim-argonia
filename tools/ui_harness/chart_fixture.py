"""ui/fixtures/chart.json's positions, made from out/chart/index.json so the mock chart agrees with the real one.

The fixture's shape stays hand-written (the schema lane's); this sets every place's id and position, the revealed
cells (a walk round Claywater Station: the 5 x 5 cells about its cell) and the views, from the index.
`--check` exits 1 if the fixture has drifted from the index (the gate's test runs it when out/chart exists).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "ui" / "fixtures" / "chart.json"
INDEX = ROOT / "out" / "chart" / "index.json"
HOME = "Claywater Station"
WALK = 2  # cells each way round the home cell


def units(ix: dict, px: float, py: float) -> tuple[float, float]:
    """Master px -> the schema's cell units (x east, y north), from the index's cell 0,0 rect."""
    _tx, _ty, x0, y0, w, h = ix["cells"]["0,0"]
    return round((px - x0) / w, 2), round((y0 + h - py) / h, 2)


def by_name(ix: dict, name: str) -> tuple[str, dict]:
    hits = sorted((k, v) for k, v in ix["places"].items() if v["name"] == name)
    if not hits:
        raise SystemExit(f"chart index has no place named {name!r}")
    return hits[0]


def made(fx: dict, ix: dict) -> dict:
    fx = json.loads(json.dumps(fx))
    hid, home = by_name(ix, HOME)
    hx, hy = home["cell"]
    hu, hv = units(ix, *home["px"])
    walk = [{"x": hx + dx, "y": hy + dy} for dx in range(-WALK, WALK + 1) for dy in range(-WALK, WALK + 1)
            if f"{hx + dx},{hy + dy}" in ix["cells"]]
    half = ix["size"] / 2
    cu, cv = units(ix, half, half)
    for name, st in fx["states"].items():
        b = st["body"]
        for p in b["places"]:
            pid, rec = by_name(ix, p["name"])
            p["id"] = pid
            p["kind"] = rec["kind"]
            p["x"], p["y"] = units(ix, *rec["px"])
            p["discovered"] = name == "claywater" and pid == hid
        if name == "claywater":
            b["revealed"] = walk
            b["view"] = {"centreX": hu, "centreY": hv, "zoom": 4}
        else:
            b["revealed"] = []
            b["view"] = {"centreX": cu, "centreY": cv, "zoom": 1}
    fx["intents"]["pan"]["body"]["view"] = {"centreX": round(hu + 3, 2), "centreY": round(hv - 1.5, 2), "zoom": 2}
    fx["doc"] = ("Mock data for 1.2's L3 harness (parchment chart). Place ids, positions and the revealed cells are "
                 "made from out/chart/index.json by tools/ui_harness/chart_fixture.py; the gate checks they agree.")
    return fx


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    fx = json.loads(FIXTURE.read_text())
    want = made(fx, json.loads(INDEX.read_text()))
    if a.check:
        if want != fx:
            print("ui/fixtures/chart.json disagrees with out/chart/index.json: run python -m tools.ui_harness.chart_fixture",
                  file=sys.stderr)
            return 1
        return 0
    FIXTURE.write_text(json.dumps(want, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
