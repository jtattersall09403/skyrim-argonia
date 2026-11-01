"""L1/L2 for 1.15 §e: the form roles, the rock sinking, the list choices and the render layer (no stack, no world)."""
import gzip
import json

import numpy as np

from tools.argonia_world import skyrim_units as su
from tools.argonia_world.vegetation import forms, layer, lists, place
from tools.argonia_world.vegetation.tests.test_vegetation import cell, rule


def test_role_reads_the_mesh_before_the_editor_id():
    assert forms.role_of("01giantmushroom", "landscape\\trees\\ztGorsebush04statwhite.nif") == "shrub"
    assert forms.role_of("x", "Vurt_Shroom\\vurt_shroom_big6.nif") == "mushroom"
    assert forms.role_of("ArgoniaRockWall01", "argonia\\mountains\\lsrockwall01.nif") == "rock"
    assert forms.role_of("XanmeerWall", "architecture\\xanmeer\\wall.nif") is None
    assert forms.role_of("TreePine", "landscape\\trees\\pine01.nif") is None  # Nordic flora never enters


def test_rock_is_sunk_by_its_bounding_box():
    flat = place.place_cell(cell(), [rule(density_per_ha=200.0)])
    sm = place.Rule.sink_of(0.38, -10, 290)  # bottom 10 units below the pivot, 300 units tall
    assert abs(sm - (-10 + 0.38 * 300) / su.UNITS_PER_METRE) < 1e-9
    sunk = place.place_cell(cell(), [rule(density_per_ha=200.0, sink_m=sm)])
    assert flat["z"].size and np.allclose(flat["z"] - sunk["z"], sunk["scale"] * sm)
    bottom = sunk["z"] + sunk["scale"] * (-10 / su.UNITS_PER_METRE)
    assert (bottom < 10.0).all()  # every bottom under the ground (10 m)
    assert place.Rule.sink_of(0.0, -10, 290) == 0.0


def test_conform_tilts_up_the_slope_sign():
    rx, ry = place.conform_rot(0.5, 0.0, 0.0)  # ground rising to the east
    assert rx == 0.0 and ry > 0


def f(**kw):
    base = {"edid": "e", "model": "m.nif", "role_id": "mushroom", "bound_z0": 0, "bound_z1": 200, "mod": "bmv"}
    base.update(kw)
    return base


def test_giant_mushrooms_and_cliffs_and_sea_plants_keep_to_their_ecology():
    giant = f(bound_z1=1000)
    assert "giant" in lists.tags(giant)
    assert lists.admits("rootland", giant) and not lists.admits("coastal-lagoon", giant)
    cliff = f(role_id="rock", bound_z1=2500)
    assert lists.admits("western-frontier", cliff) and not lists.admits("rootland", cliff)
    assert lists.sink_frac(cliff) == lists.SINK_CLIFF and lists.sink_frac(f(role_id="rock")) == lists.SINK_BOULDER
    kelp = f(role_id="aquatic", model="Landscape\\Grass\\WaterKelpTall01.nif")
    assert lists.admits("tidal-delta", kelp) and not lists.admits("interior-swamp", kelp)


def test_pick_keeps_the_core_and_varies_the_tail_by_packet():
    pool = list(range(20))
    a, b = lists.pick(pool, 8, "hist-heartland"), lists.pick(pool, 8, "saxhleel-coast")
    assert a[:3] == b[:3] == [0, 1, 2] and len(a) == 8 and a != b


def test_render_layer_colours_by_role(tmp_path):
    class W:
        def query(self, sql, *a):
            return [{"form_key": "000001:Black Marsh.esm", "role_id": "rock"}]
    line = {"x": 0, "y": 0, "region": "r", "bases": ["000001:Black Marsh.esm"],
            "refs": [[1, 0, 10.0, 20.0, 0.0, 0, 0, 0, 1.0]]}
    with gzip.open(tmp_path / "cy+000.jsonl.gz", "wt") as g:
        g.write(json.dumps(line) + "\n")
    out = layer.render_layer((0, 0, 0, 0), out=tmp_path, world=W())
    assert out["role"] == ["rock"] and tuple(out["rgb"][0]) == layer.COLOURS["rock"]
