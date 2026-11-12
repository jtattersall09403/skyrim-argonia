"""The regions' identity sheets (tools/newworld/identity.py): the committed sheet passes, and the measures catch
neighbours that are too alike."""
from __future__ import annotations

import copy

from tools.newworld import identity as I


def test_committed_sheet_has_every_region_and_passes():
    sheet, pairs = I.load(), I.adjacency()
    assert len(sheet["regions"]) == 24 and len(pairs) >= 50
    assert I.faults(sheet, pairs) == []


def test_identical_neighbours_fail_and_three_differences_pass():
    sheet = I.load()
    a = sheet["regions"]["murkwood"]
    twin = copy.deepcopy(a)
    s = {"sound_beds": sheet["sound_beds"], "water_looks": sheet["water_looks"], "ground_families": sheet["ground_families"],
         "regions": {"a": a, "b": twin}}
    twin["slot"] = 99
    assert any("differ on 0 of 6" in f for f in I.faults(s, [("a", "b")], ecology=None))
    twin["sight"]["visibility"] = round(a["sight"]["visibility"] * 1.5, 3)
    twin["water"]["look"] = "turquoise"
    assert any("differ on 2 of 6" in f for f in I.faults(s, [("a", "b")], ecology=None))
    twin["ground"]["family"] = "pink"
    assert I.faults(s, [("a", "b")], ecology=None) == []


def test_light_counts_hue_or_luminance_not_near_grey_hue():
    base = {"haze": [150, 150, 150], "brightness": 1.0}
    grey2 = {"haze": [150, 152, 156], "brightness": 1.0}
    row = lambda light: {"light": light, "sight": {"visibility": 1}, "weather": {"chances": {"fair": 1}},
                         "sound": {"day": "x", "night": "y"}, "ground": {"family": "f"}, "water": {"look": "w"}}
    assert not I.differences(row(base), row(grey2))["light"][0]
    assert I.differences(row(base), row({**base, "brightness": 1.35}))["light"][0]
    assert I.differences(row({"haze": [200, 120, 80], "brightness": 1}), row({"haze": [90, 160, 90], "brightness": 1}))["light"][0]
