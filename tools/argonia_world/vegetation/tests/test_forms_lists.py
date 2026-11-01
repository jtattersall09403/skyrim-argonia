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


def test_own_rock_forms_vary_by_region_family():
    from tools.argonia_world.vegetation import rocks
    az = f(role_id="rock", model=rocks.ROCKS[0][1], bound_z1=200)
    al = f(role_id="rock", model=rocks.ROCKS[10][1], bound_z1=200)
    assert lists.admits("northern-transition", az) and not lists.admits("western-frontier", az)
    assert lists.admits("western-frontier", al) and not lists.admits("northern-transition", al)
    assert len({i for i, _, _ in rocks.ROCKS}) == len(rocks.ROCKS)  # one FormID each, appended only
    assert rocks.form_key(0) == "0C0000:ArgoniaWorld.esm" and rocks.edid(rocks.ROCKS[0][1]) == "ARG_Rock_az_rock02"


def test_pick_below_the_core_rotates_by_packet():
    pool = list(range(8))
    a, b = lists.pick(pool, 2, "hist-heartland"), lists.pick(pool, 2, "saxhleel-coast")
    assert len(a) == len(b) == 2 and a != b


def test_navmesh_water_from_cell_water_levels():
    from tools.navmesh import inputs

    class CW:
        def level(self, cx, cy):
            return 2.0 if (cx, cy) == (0, 0) else None
    x0u, ytop = su.cell_origin(0, 0)[0], su.cell_origin(0, 0)[1] + su.CELL_UNITS
    lv = inputs.cell_levels((0, 0, 1, 0), (su.LAND_VERTS, 2 * su.LAND_VERTS - 1), x0u, ytop, CW())
    assert np.allclose(lv[:, :su.LAND_VERTS], su.metres_to_units(2.0)) and np.isneginf(lv[:, su.LAND_VERTS:]).all()


def test_climbable_collision_by_role():
    # Free Climb's stable set (climb-anything.md section 1): rock Static/Terrain, tree Static/Trees/Terrain, mass 0
    assert forms.climbable("rock", 1, 0.0) and forms.climbable("rock", 13, 0.0)
    assert not forms.climbable("rock", forms.NO_BODY, 0.0)  # 74 of 312 BM&V landscape rocks have no body
    assert not forms.climbable("rock", 1, 1.0)  # IvyPine: a mass-1 body is dynamic
    assert not forms.climbable("rock", None, None)  # never measured
    assert forms.climbable("canopy", 9, 0.0) and forms.climbable("canopy", 1, 0.0)
    assert not forms.climbable("canopy", 15, 0.0) and not forms.climbable("palm", forms.NO_BODY, 0.0)
    assert forms.climbable("shrub", 15, 0.0) and forms.climbable("aquatic", forms.NO_BODY, 0.0)  # plants stay flora


def test_lists_drop_forms_with_no_climbable_body():
    from tools.argonia_world import db
    w = db.open()
    for r in w.query("SELECT o.form_key, f.role_id, f.collision_layer l, f.collision_mass m FROM land_region_object o "
                     "JOIN object_form f USING (form_key)"):
        assert forms.climbable(r["role_id"], r["l"], r["m"]) or (r["l"] is None and r["role_id"] != "rock"), r["form_key"]
