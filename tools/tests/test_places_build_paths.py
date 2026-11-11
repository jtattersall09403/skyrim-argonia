"""The builder's path painting: the world's road rule (tools/newworld/world/roadpaint.py) on the world's own ground."""
import base64

import numpy as np
import pytest

from tools.places import build
from tools.newworld.world import roadpaint as rp

W = "ArgoniaNewWorld.esm:"
NAMES = ["gravel_track", "mud_track", "verge", "swamp_mud", "forest_floor", "moss", "rock", "sand", "meadow", "silt"]
LTEX = [{"edid": f"ANW_Ground_{n}", "fk": f"{W}{900 + i:06X}"} for i, n in enumerate(NAMES)]
KEY = {n: f"{W}{900 + i:06X}" for i, n in enumerate(NAMES)}
LINE = [[100.0, 100.0], [900.0, 100.0]]
FLAT = base64.b64encode(bytes(33 * 33)).decode()


def world_layers(textures):
    """A world LAND's layers: in each quadrant the first texture as base, the rest as alpha layers of 0.3 everywhere."""
    out = []
    for q in range(4):
        out.append({"quadrant": q, "layer": 0xFFFF, "texture": KEY[textures[0]], "alpha": None})
        for k, t in enumerate(textures[1:]):
            out.append({"quadrant": q, "layer": k, "texture": KEY[t], "alpha": [[i, 0.3] for i in range(289)]})
    return out


def facts(textures=("forest_floor",), offset=5.0):
    return {"ltex": LTEX, "by_cell": {(x, y): {"x": x, "y": y, "water": 0.0, "offset": offset, "deltas": FLAT,
                                                "layers": world_layers(textures)} for x in (-1, 0) for y in (-1, 0)}}


@pytest.fixture(autouse=True)
def forest_ground(monkeypatch):
    monkeypatch.setattr(build, "path_road_set", lambda x, y: rp.ROAD_SETS["forest"])
    build.PROBLEMS.clear()


def plan(style, f=None, width=160):
    return build.plan_paths([{"id": "p.1", "kind": "path", "style": style, "points": LINE, "width": width}], f or facts())


def composite(quad):
    """A planned quadrant -> {texture key: weights [289]} as the engine stacks it."""
    w = {quad["base"]: np.ones(289)}
    for la in quad["layers"]:
        o = np.zeros(289)
        for i, op in la["alpha"]:
            o[i] = op
        for k in w:
            w[k] = w[k] * (1 - o)
        w[la["texture"]] = w.get(la["texture"], np.zeros(289)) + o
    return w


def test_a_style_word_takes_its_grounds_road_set_and_never_more_than_six_textures():
    out = plan("dirt", facts(("forest_floor", "moss", "rock", "sand", "meadow", "silt")))
    assert not build.PROBLEMS
    used = {k for quads in out.values() for q in quads for k in [q["base"]] + [la["texture"] for la in q["layers"]]}
    assert {KEY["gravel_track"], KEY["mud_track"], KEY["verge"]} <= used
    assert all(1 + len(q["layers"]) <= 6 for quads in out.values() for q in quads)


def test_the_path_ramps_over_two_vertices_or_more_and_is_full_on_its_line():
    out = plan("dirt")
    q = next(q for q in out[(0, 0)] if q["quadrant"] == 0)  # BL of cell 0,0: the line runs along y = 100
    w = composite(q)
    road = sum(w.get(KEY[n], 0) for n in rp.ROAD_SETS["forest"]).reshape(17, 17)
    col = road[:, 4]  # x = 512, y from the south: vertices 0 (y 0), 1 (y 128), 2 (256), 3 (384) ...
    assert col[1] > 0.95                                    # 28 units off the line: on the path
    steps = np.abs(np.diff(col))
    assert steps.max() <= 0.5                               # no one-vertex edge
    assert 0 < col[4] < 0.25 and col[5] > 0 and col[6] == 0  # 412 and 540 units off: the ramp's tail; 668 off: past its reach (80 + 479)


def test_a_texture_picked_by_key_is_the_one_painted():
    out = plan(KEY["swamp_mud"])
    used = {la["texture"] for quads in out.values() for q in quads for la in q["layers"]} | {q["base"] for quads in out.values() for q in quads}
    assert KEY["swamp_mud"] in used and KEY["gravel_track"] not in used
    out = plan("Black Marsh.esm:0A1B2C")   # a master's own road texture
    assert not build.PROBLEMS and any(la["texture"] == "Black Marsh.esm:0A1B2C" for quads in out.values() for q in quads for la in q["layers"])


def test_a_texture_of_a_plugin_that_is_not_loaded_is_a_listed_problem():
    out = plan("Some Mod.esp:000123")
    assert out == {} and len(build.PROBLEMS) == 1 and "Some Mod.esp:000123" in build.PROBLEMS[0]


def test_a_quadrant_keeps_the_world_ground_on_its_border_where_the_path_does_not_reach():
    out = plan("dirt", facts(("forest_floor", "moss")))
    q = next(q for q in out[(0, 0)] if q["quadrant"] == 0)  # BL of cell 0,0: its north edge (y 2048) is shared with the untouched TL
    w = composite(q)
    top = slice(16 * 17, 17 * 17)   # its north edge, shared with the untouched cell to the north
    assert abs(w[KEY["forest_floor"]][top] - 0.7).max() < 2 / 255 and abs(w[KEY["moss"]][top] - 0.3).max() < 2 / 255


def test_a_boardwalk_is_painted_only_where_its_line_is_on_dry_land():
    def painted(offset_steps):
        build.PROBLEMS.clear()
        return bool(build.plan_paths([{"id": "p.1", "kind": "walkway", "style": "boardwalk", "points": LINE,
                                       "width": 160}], facts(offset=offset_steps)))
    assert painted(5.0)        # the land stands 40 units over the water: the path is on the ground
    assert not painted(-5.0)   # the bed lies 40 units under it: the line is a deck's, nothing is painted
