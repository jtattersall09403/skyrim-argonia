"""ui/fixtures/chart.json's states and hud.json's minimap states, made from out/chart/index.json so the mock chart
agrees with the real one.

The fixture's shape stays hand-written (the schema lane's); this sets every place's id and position, the revealed
cells (a walk round Claywater Station: the cells within 6 of its cell) and the views, from the index.
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
HOME_FORM = "0A000801"  # a stand-in map marker form id
WALK = 2  # cells each way round each step of the walk
PATH = 4  # the walk's steps east from the home cell (a few minutes on foot)
HUD = ROOT / "ui" / "fixtures" / "hud.json"


def units(ix: dict, px: float, py: float) -> tuple[float, float]:
    """Master px -> the schema's cell units (x east, y north), from the index's cell 0,0 rect."""
    _tx, _ty, x0, y0, w, h = ix["cells"]["0,0"]
    return round((px - x0) / w, 2), round((y0 + h - py) / h, 2)


def by_name(ix: dict, name: str) -> tuple[str, dict]:
    hits = sorted((k, v) for k, v in ix["places"].items() if v["name"] == name)
    if not hits:
        raise SystemExit(f"chart index has no place named {name!r}")
    return hits[0]


def walked(ix: dict, hx: int, hy: int) -> list[dict]:
    """The cells within WALK of each step of a short walk east-north-east from the home cell (a walked path)."""
    out: dict[str, dict] = {}
    for s in range(PATH + 1):
        cx, cy = hx + s, hy + s // 3
        for dx in range(-WALK, WALK + 1):
            for dy in range(-WALK, WALK + 1):
                k = f"{cx + dx},{cy + dy}"
                if dx * dx + dy * dy <= WALK * WALK and k in ix["cells"]:
                    out[k] = {"x": cx + dx, "y": cy + dy}
    return sorted(out.values(), key=lambda c: (c["x"], c["y"]))


def made(fx: dict, ix: dict) -> dict:
    """chart.json's states and hud.json's minimap states, from the index.

    unexplored  the whole province, nothing revealed, the player at home;
    whole       full zoom-out after the walk: the revealed path, Claywater's marker, the player at the walk's end;
    walked      zoomed to the player before Claywater's discovery: the land revealed, no marker;
    claywater   the same after its discovery: the marker shows."""
    fx = json.loads(json.dumps(fx))
    hid, home = by_name(ix, HOME)
    hx, hy = home["cell"]
    hu, hv = units(ix, *home["px"])
    walk = walked(ix, hx, hy)
    place = {"id": HOME_FORM, "name": home["name"], "kind": home["kind"], "x": hu, "y": hv}
    player = {"x": round(hx + PATH + 0.5, 2), "y": round(hy + PATH // 3 + 0.5, 2), "heading": 45}
    half = ix["size"] / 2
    cu, cv = units(ix, half, half)
    close = {"centreX": player["x"], "centreY": player["y"], "zoom": 4}  # under ZOOM_MAX (8) by the zoom step
    states = {
        "unexplored": ([], [], {**player, "x": hu, "y": hv, "heading": 0}, {"centreX": cu, "centreY": cv, "zoom": 1}),
        "whole": (walk, [place], player, {"centreX": cu, "centreY": cv, "zoom": 1}),
        "walked": (walk, [], player, close),
        "claywater": (walk, [place], player, close),
    }
    fx["states"] = {name: {"type": "chart.state", "v": 2, "body": {
        "worldspace": "argonia", "sketch": "chart.sketch", "revealed": r, "places": pl, "player": me, "view": v}}
        for name, (r, pl, me, v) in states.items()}
    fx["intents"]["pan"]["body"]["view"] = {"centreX": round(hu + 3, 2), "centreY": round(hv - 1.5, 2), "zoom": 2}
    fx["doc"] = ("Mock data for the L3 harness (parchment chart, 1.12 §5). Positions, the walked cells and the "
                 "views are made from out/chart/index.json by tools/ui_harness/chart_fixture.py; the gate checks they agree.")
    return fx


def minimap_states(ix: dict) -> dict:
    """hud.json's minimap pushes: the chart round the player after the walk, facing north and then 135 degrees."""
    c = made({"states": {}, "intents": {"pan": {"body": {}}}}, ix)["states"]["claywater"]["body"]
    me = c["player"]
    reach = 5  # skse/core chart::kMinimapReach

    def near(x: float, y: float) -> bool:
        nx, ny = min(max(me["x"], x), x + 1), min(max(me["y"], y), y + 1)
        return (nx - me["x"]) ** 2 + (ny - me["y"]) ** 2 <= reach * reach
    rev = [k for k in c["revealed"] if near(k["x"], k["y"])]
    pl = [p for p in c["places"] if (p["x"] - me["x"]) ** 2 + (p["y"] - me["y"]) ** 2 <= reach * reach]
    return {f"minimap{h}": {"type": "hud.minimap", "v": 1, "body": {"map": {
        "player": {**me, "heading": h}, "revealed": rev, "places": pl}}} for h in (0, 135)}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    ix = json.loads(INDEX.read_text())
    fx, hud = json.loads(FIXTURE.read_text()), json.loads(HUD.read_text())
    want = made(fx, ix)
    want_hud = {**hud, "states": {k: v for k, v in hud["states"].items() if not k.startswith("minimap")} | minimap_states(ix)}
    if a.check:
        if want != fx or want_hud != hud:
            print("ui/fixtures/chart.json or hud.json disagrees with out/chart/index.json: run python -m "
                  "tools.ui_harness.chart_fixture", file=sys.stderr)
            return 1
        return 0
    FIXTURE.write_text(json.dumps(want, indent=1) + "\n")
    HUD.write_text(json.dumps(want_hud, indent=1, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
