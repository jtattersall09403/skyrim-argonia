"""The measured pairing of light sources and their lights (tools/places/light_pairs.py), used by the lights stage
(draft/lights.py station_lights) and the agent's `look place`."""
import math

from tools.places import light_pairs as lp
from tools.places.draft import lights


def test_table_keeps_bases_placed_with_a_light_and_says_why_others_are_left_out():
    ev = {"plugins": [], "lights": 9, "bound": 8, "bases": [
        {"base": "S:1", "edid": "CandleHorn", "type": "STAT", "placed": 10,
         "lights": [["L:1", 0, 0, 10], ["L:1", 0, 0, 12], ["L:2", 0, 0, 30], ["L:1", 2, 0, 11]]},
        {"base": "S:2", "edid": "Crate01", "type": "STAT", "placed": 400, "lights": [["L:1", 50, 0, 0]]},
        {"base": "S:3", "edid": "LanternGlow", "type": "STAT", "placed": 12, "lights": []}]}
    t, left = lp.table(ev)
    assert t == {"S:1": {"light": "L:1", "offset": [0, 0, 11], "lit": 4, "placed": 10, "edid": "CandleHorn"}}
    assert [r["base"] for r in left] == ["S:3"] and "never placed with a light" in left[0]["why"]


def test_the_committed_table_lights_a_burning_campfire():
    t = lp.pairs()
    assert len(t) > 100
    fire = t["Skyrim.esm:035F49"]   # Campfire01Burning
    assert fire["lit"] >= 50 and fire["offset"][2] > 40


def test_an_added_light_source_carries_its_light_turned_with_it():
    fix = {"id": "p.F", "base": "Skyrim.esm:05D6EA", "kind": "static", "pos": [100.0, 200.0, 300.0],
           "rot": [0.0, 0.0, math.pi / 2], "scale": 1.0, "layer": "place"}
    off = lp.pairs()["Skyrim.esm:05D6EA"]["offset"]
    row = lp.light_row(fix, "p.L")
    # a quarter clockwise turn takes the fixture's +X to -Y and its +Y to +X
    assert abs(row["pos"][0] - (100 + off[1])) < 0.02 and abs(row["pos"][1] - (200 - off[0])) < 0.02
    assert row["seat"] == {"mode": "on", "on": "p.F", "dz": round(off[2], 2)}
    got = lights.station_lights("p", [fix], {})
    assert len(got) == 1 and got[0]["base"] == row["base"] and got[0]["seat"]["on"] == "p.F"
    # a source row, or one already lit, gets none
    assert lights.station_lights("p", [dict(fix, src="s.1")], {}) == []
    assert lights.station_lights("p", [fix, dict(row, id="x")], {}) == []
