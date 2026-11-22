"""A place's ground paint (tools/places/paint.py): the rule, its studio fixture, the save ops, and the build laying it
into the quadrants' land texture layers under the six-texture limit."""
import json
import os
from pathlib import Path

import numpy as np
import pytest

from tools.places import build, edits, paint
from tools.tests.test_places_build_paths import KEY, composite, facts

REPO = Path(__file__).resolve().parents[2]
FIXTURE = REPO / "tools/places/studio/web/test/paint_rule.json"
MUD, SAND, MOSS = KEY["swamp_mud"], KEY["sand"], KEY["moss"]

ROWS = [
    {"id": "paint.0001", "texture": MUD, "brush": "soft", "size": 600, "softness": 0.5, "strength": 1.0,
     "points": [[-3000, -3000, 1.0], [-1000, -2500, 0.4], [-500, -400, 0.8]]},
    {"id": "paint.0002", "texture": SAND, "brush": "hard", "size": 300, "strength": 0.7, "points": [[-2000, -2000, 1.0]]},
    {"id": "paint.0003", "texture": MOSS, "brush": "scatter", "size": 900, "softness": 0.3, "seed": 7,
     "points": [[-1500, -1200, 1.0], [-200, -300, 1.0]]},
    {"id": "paint.0004", "erase": True, "brush": "soft", "size": 250, "points": [[-1000, -2500, 1.0]]},
    {"id": "paint.0005", "texture": SAND, "brush": "soft", "size": 400, "softness": 0.4,
     "polygon": [[-3900, -800], [-2600, -900], [-2800, -100], [-3700, -200]]},
]


def paint_rule_fixture() -> dict:
    """The rule's numbers at fixed rows, for the studio's paint_rule.js (node reads the file; this proves it)."""
    r6 = lambda o: json.loads(json.dumps(o), parse_float=lambda x: round(float(x), 5))
    P, W = paint.cell_paint(ROWS, (-1, -1))
    pts = [[-3000, -3000], [-1000, -2500], [-2000, -2000], [-896, -768], [-3200, -512], [-128, -128], [-2560, -1408]]
    covers = [[float(paint.cover(r, np.array([float(x)]), np.array([float(y)]))[0]) for x, y in pts] for r in ROWS]
    return r6({"rows": ROWS, "points": pts, "covers": covers, "cell": [-1, -1], "total": P.ravel().tolist(),
               "weights": {k: v.ravel().tolist() for k, v in sorted(W.items())}})


def test_the_studio_fixture_is_what_the_rule_gives():
    want = paint_rule_fixture()
    if os.environ.get("ARGONIA_WRITE_FIXTURES") or not FIXTURE.exists():
        FIXTURE.write_text(json.dumps(want) + "\n")
    assert json.loads(FIXTURE.read_text()) == want


def test_brushes_hard_soft_and_pressure():
    X, Y = np.array([0.0, 280.0, 320.0, 500.0]), np.zeros(4)
    hard = paint.cover({"id": "a", "texture": MUD, "brush": "hard", "size": 300, "points": [[0, 0, 1]]}, X, Y)
    assert hard.tolist() == [1.0, 1.0, 0.0, 0.0]
    soft = paint.cover({"id": "a", "texture": MUD, "brush": "soft", "size": 300, "softness": 1.0, "points": [[0, 0, 1]]}, X, Y)
    assert soft[0] == 1.0 and 0 < soft[1] < 0.1 and soft[2] == 0
    light = paint.cover({"id": "a", "texture": MUD, "brush": "hard", "size": 300, "points": [[0, 0, 0.0]]}, X, Y)
    assert light.tolist() == [0.5, 0.0, 0.0, 0.0]   # no pressure: a third of the radius, half the opacity


def test_scatter_breaks_the_brush_into_patches():
    gx, gy = np.meshgrid(np.arange(-20, 20) * 128.0, np.arange(-20, 20) * 128.0)
    v = paint.cover({"id": "a", "texture": MUD, "brush": "scatter", "size": 5000, "softness": 0, "seed": 3,
                     "points": [[0, 0, 1]]}, gx, gy)
    assert 0.15 < (v > 0.5).mean() < 0.85 and (v == 0).any()


def test_erase_gives_the_world_back_and_order_is_by_id():
    rows = [{"id": "paint.0001", "texture": MUD, "brush": "hard", "size": 2000, "points": [[2048, 2048, 1]]},
            {"id": "paint.0002", "erase": True, "brush": "hard", "size": 2000, "points": [[2048, 2048, 1]]}]
    assert paint.cell_paint(rows, (0, 0))[0].max() == 0
    assert paint.cell_paint(rows[::-1], (0, 0))[0].max() == 0   # the file's order never matters, the ids do
    assert paint.next_id(rows) == "paint.0003"


def test_a_bad_row_is_named():
    for row, msg in (({"id": "p", "points": [[0, 0, 1]]}, "land texture"),
                     ({"id": "p", "texture": MUD, "brush": "fat", "points": [[0, 0]]}, "brush"),
                     ({"id": "p", "texture": MUD, "polygon": [[0, 0], [1, 1]]}, "three"),
                     ({"id": "p", "texture": MUD}, "either")):
        with pytest.raises(paint.PaintError, match=msg):
            paint.check_row(row)


def test_a_save_adds_and_removes_paint_and_its_inverse_restores():
    files = edits.canonical({"place": {}, "spaces": {}})
    op = {"n": 1, "op": "paint.add", "paint": ROWS[0]}
    edits.check_op(op)
    out = edits.apply(files, [op])
    assert out["paint"] == [ROWS[0]]
    back = edits.apply(out, [edits.inverse(op)])
    assert "paint" not in back
    with pytest.raises(edits.EditError):
        edits.check_op({"n": 2, "op": "paint.add", "paint": {"id": "paint.0009", "points": [[0, 0]]}})


def test_the_build_lays_the_paint_into_the_quadrants():
    build.PROBLEMS.clear()
    rows = [{"id": "paint.0001", "texture": MUD, "brush": "hard", "size": 700, "points": [[-2048, -2048, 1.0]]}]
    out = build.plan_paths([], facts(("forest_floor", "moss")), None, rows)
    assert not build.PROBLEMS, build.PROBLEMS
    quads = {q["quadrant"]: q for q in out[(-1, -1)]}
    # the centre of cell -1,-1 is the corner the four quadrants share: index 288 of BL, 0 of TR
    assert composite(quads[0])[MUD][288] > 0.99 and composite(quads[3])[MUD][0] > 0.99
    w = composite(quads[0])
    assert w[MUD][0] < 0.01 and w[KEY["forest_floor"]][0] > 0.5   # the far corner keeps the world's paint
    assert all(1 + len(q["layers"]) <= 6 for qs in out.values() for q in qs)


def test_seven_painted_textures_in_one_quadrant_fail_clearly():
    build.PROBLEMS.clear()
    names = ["gravel_track", "mud_track", "verge", "swamp_mud", "moss", "rock", "sand"]
    rows = [{"id": f"paint.{i + 1:04d}", "texture": KEY[n], "brush": "hard", "size": 300,
             "points": [[-3900 + i * 260, -3900, 1.0]]} for i, n in enumerate(names)]
    build.plan_paths([], facts(("forest_floor",)), None, rows)
    assert any("cannot keep painted" in p for p in build.PROBLEMS)
    build.PROBLEMS.clear()
    build.plan_paths([], facts(("forest_floor",)), None, [dict(rows[0], texture="Nowhere.esp:000001")])
    assert any("no plugin" in p for p in build.PROBLEMS)
