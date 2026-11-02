"""L2 (1.15 build speed): the vegetation band cache. A band's key covers every placement input and its rules; an
equal key reloads the placed stems, any changed input (or a stale stored key) misses."""
import numpy as np

from tools.argonia_world.vegetation import build, place
from tools.argonia_world.vegetation.tests.test_vegetation import V, cell, rule


def _band(h=10.0, feet=()):
    H = h + np.add.outer(np.arange(V), np.arange(V)) * 0.05
    return [cell(H=H, cx=cx, cy=5, feet=feet) for cx in (-3, -2)]


def test_band_key_covers_inputs_and_rules():
    rules, region = {"r": [rule()]}, {(-3, 5): "r", (-2, 5): "r"}
    k = build.band_key(_band(), rules, region)
    assert k == build.band_key(_band(), rules, region)
    assert k != build.band_key(_band(h=11.0), rules, region)  # the ground
    assert k != build.band_key(_band(feet=[(1, 2, 3, 4)]), rules, region)  # a place footprint
    assert k != build.band_key(_band(), {"r": [rule(density_per_ha=61.0)]}, region)  # a rule row


def test_cached_band_equals_a_fresh_placement_and_a_stale_key_misses(tmp_path):
    rules, region = {"r": [rule()]}, {(-3, 5): "r", (-2, 5): "r"}
    cis = _band()
    k = build.band_key(cis, rules, region)
    got = {(c.cx, c.cy): place.place_cell(c, rules["r"]) for c in cis}
    build.save_band(tmp_path, 5, k, got)
    back = build.load_band(tmp_path, 5, k)
    for c in got:
        for f in got[c]:
            assert np.array_equal(back[c][f], place.place_cell(cis[0 if c[0] == -3 else 1], rules["r"])[f])
    assert build.load_band(tmp_path, 5, "stale") is None
    assert build.load_band(tmp_path, 6, k) is None
