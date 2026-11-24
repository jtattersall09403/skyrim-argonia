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
    assert t == {"S:1": {"light": "L:1", "offset": [0, 0, 11], "how": "measured", "lit": 4, "placed": 10,
                         "edid": "CandleHorn", "class": "flame"}}
    assert [r["base"] for r in left] == ["S:3"] and "no mesh" in left[0]["why"]


def test_never_lit_sources_take_their_class_light_at_their_own_mesh_offset_and_unlit_ones_are_named_out():
    ev = {"plugins": [], "lights": 9, "bound": 8, "bases": [
        {"base": "S:1", "edid": "CandleHorn", "model": "horn.nif", "type": "STAT", "placed": 10,
         "lights": [["L:1", 0, 0, 10], ["L:1", 0, 0, 12], ["L:1", 2, 0, 11]]},
        {"base": "S:2", "edid": "CandleLantern02", "model": "candle2.nif", "type": "STAT", "placed": 3, "lights": []},
        {"base": "S:3", "edid": "CandleLampOff", "model": "off.nif", "type": "STAT", "placed": 3, "lights": []},
        {"base": "S:4", "edid": "FirewoodPile01", "model": "wood.nif", "type": "STAT", "placed": 3, "lights": []},
        {"base": "S:5", "edid": "RareCandle", "model": "r.nif", "type": "STAT", "placed": 40, "lights": [["L:2", 1, 1, 30]]}]}
    meshes = {"horn.nif": ([0, 0, 0], 40.0), "candle2.nif": ([1.0, 2.0, 33.0], 45.0)}
    t, left = lp.table(ev, lambda m: meshes.get(m))
    assert t["S:2"] == {"light": "L:1", "offset": [1.0, 2.0, 33.0], "how": "by class", "lit": 0, "placed": 3,
                        "edid": "CandleLantern02", "class": "flame", "like": "S:1"}
    assert t["S:5"]["how"] == "measured, rarely" and t["S:5"]["light"] == "L:2"
    assert {r["base"]: r["why"].split(" (")[0] for r in left} == {"S:3": "an unlit variant", "S:4": "not a light source"}


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


def test_a_second_run_keeps_the_lights_the_first_added():
    """The lights stage's own lights never count as a source already lit: running it again keeps them (it had dropped
    them, and a third run added them back)."""
    from tools.places.draft import lights
    fix = {"id": "p.F", "base": "Skyrim.esm:05D6EA", "kind": "static", "pos": [100.0, 200.0, 300.0],
           "rot": [0.0, 0.0, 0.0], "scale": 1.0, "layer": "place"}
    first = lights.station_lights("p", [fix], {})
    assert len(first) == 1
    again = lights.station_lights("p", [fix, *first], {}, {r["id"] for r in first})
    assert [r["id"] for r in again] == [r["id"] for r in first]
    assert lights.station_lights("p", [fix, *first], {}) == []   # a light the stage did not add does count as lit
