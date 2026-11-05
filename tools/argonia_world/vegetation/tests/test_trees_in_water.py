"""L1: no tree or large shrub in the water (lane 1.15-r6-trees-in-water): the placer's rule and the census."""
import numpy as np

from tools.argonia_world import skyrim_units as su
from tools.argonia_world.vegetation import census, place
from tools.argonia_world.vegetation.place import CellInputs, Rule

V = su.LAND_VERTS


def rule(**kw):
    base = dict(form_key="000001:Skyrim.esm", density_per_ha=400.0, clustering=1, radius_m=0.0, min_slope=0,
                max_slope=40, min_height=None, max_height=None, water_min=-6.0, water_max=1.2, conform=False,
                scale=(1.0, 1.0), tree=True, stem=True)
    base.update(kw)
    return Rule(**base)


def shore(level=0.0):
    """Ground rising east from 1 m under the level to 2 m over it, the water's edge mid-cell."""
    j = np.linspace(-1.0, 2.0, V)[None, :]
    return np.repeat(j, V, axis=0) + level


def cell(H, wtype, level=0.0):
    return CellInputs(0, 0, H, np.full((V, V), level), np.full((V, V), level), np.zeros((V, V), bool),
                      south_row=1000, west_col=1000, roads=[], footprints=[], wtype=wtype)


def test_no_stem_in_the_sea_or_within_a_metre_of_it():
    H = shore()
    p = place.place_cell(cell(H, "sea"), [rule()])
    assert p["u"].size > 10
    za, zb, *_ = place.ground_at(H, p["u"], p["v"])
    assert ((za + zb) / 2 >= 0).all()
    assert not place.wet_near(H, 0.0, p["u"], p["v"]).any()
    # the rule is what refuses them: without it the posture let trunks stand in 1.2 m
    q = place.place_cell(cell(H, "sea"), [rule(stem=False)])
    za, zb, *_ = place.ground_at(H, q["u"], q["v"])
    assert ((za + zb) / 2 < 0).any()


def test_cypress_and_mangrove_stand_in_black_water_only():
    H = shore()
    wet = lambda p: (lambda za, zb: ((za + zb) / 2 < 0).sum())(*place.ground_at(H, p["u"], p["v"])[:2])  # noqa: E731
    assert wet(place.place_cell(cell(H, "blackwater"), [rule(in_water=True)])) > 0
    for wt in ("sea", "brackish", "fresh"):
        assert wet(place.place_cell(cell(H, wt), [rule(in_water=True)])) == 0
    assert wet(place.place_cell(cell(H, "blackwater"), [rule()])) == 0  # a pine is no cypress


def test_stem_and_water_tree_classes():
    assert place.is_stem({"role_id": "canopy"})
    assert not place.is_stem({"role_id": "aquatic"}) and not place.is_stem({"role_id": "rock"})
    assert place.is_stem({"role_id": "shrub", "bound_z0": 0, "bound_z1": 200})
    assert not place.is_stem({"role_id": "shrub", "bound_z0": 0, "bound_z1": 60})
    assert place.in_water_ok({"role_id": "canopy", "model": "trees/cypress01.nif", "edid": "X"}, "blackwater")
    assert place.in_water_ok({"role_id": "mangrove", "model": "", "edid": ""}, "blackwater")
    assert not place.in_water_ok({"role_id": "mangrove", "model": "", "edid": ""}, "sea")
    assert not place.in_water_ok({"role_id": "canopy", "model": "pine.nif", "edid": "Pine"}, "blackwater")


def test_census_marks_a_stem_in_the_water_and_one_by_it():
    H = np.full((V, V), 1.0)
    H[:, :11] = -0.5  # the water's edge between vertex columns 10 (wet) and 11 (dry)
    s = su.VERTEX_SPACING_UNITS
    u = np.array([5 * s, 10.4 * s, 12.0 * s])  # in the water; on dry ground 0.73 m from a wet vertex; dry
    wet, depth = census.cell_census(H, 0.0, u, np.full(3, 3.1 * s))
    assert wet.tolist() == [True, True, False]
    assert depth[0] > 0 and depth[1] < 0
