"""Hostile people and toughness of the ecology stage (tools/newworld/ecology/people.py, toughness.py): looks are whole
non-Nord bandit-faction records, kit rises with the band's tier and is never Nordic, damage is the band's and the size
class's alone and rises with the band, and what is committed in bindings.json holds to the same rules."""
import json
from pathlib import Path

from tools.newworld.ecology import people as P
from tools.newworld.ecology import toughness as T

REPO = Path(__file__).resolve().parents[2]
BASE = {"insect": 5.0, "small": 5.0, "game": 11.25, "predator": 35.0, "giant": 65.0}


def npc(edid, race="R1", female=False, voice="V1", fact=("F1",), **kw):
    return {"key": f"{edid}:x", "edid": edid, "race": race, "vtck": voice, "tplt": None, "female": female,
            "unique": False, "lvl": 5, "tf": 0, "fact": list(fact), **kw}


EDIDS = {"R1": "RedguardRace", "R2": "ImperialRace", "V1": "MaleEvenToned", "V2": "MaleNord", "F1": "BanditFaction",
         "F2": "TownFaction"}


def test_looks_are_whole_hostile_non_nord_records():
    assert P.eligible(npc("EncBanditA"), "redguard", EDIDS)
    assert not P.eligible(npc("EncBanditA", race="R2"), "redguard", EDIDS)            # another race
    assert not P.eligible(npc("EncBanditA", voice="V2"), "redguard", EDIDS)           # a Nord voice
    assert not P.eligible(npc("EncBanditA", fact=("F2",)), "redguard", EDIDS)         # not hostile
    assert not P.eligible(npc("EncBanditA", unique=True), "redguard", EDIDS)          # a named person
    assert not P.eligible(npc("EncBanditA", tf=1, tplt="T:x"), "redguard", EDIDS)     # face from a template list
    assert not P.eligible(npc("EncBanditGhostA"), "redguard", EDIDS)


def test_pick_looks_mixes_sexes_and_differs_by_group():
    pool = [npc(f"Enc{i}{'F' if i % 2 else 'M'}", female=bool(i % 2)) for i in range(12)]
    got = P.pick_looks(pool, "redguard", 4, "g1", EDIDS)
    assert len(got) == 4 and {x["female"] for x in got} == {True, False}
    assert [x["edid"] for x in got] != [x["edid"] for x in P.pick_looks(pool, "redguard", 4, "g2", EDIDS)]


def test_kit_set_value_and_pieces():
    vals = {e: 10 for e in P.ARMOUR["iron"] + ["IronSword", "ArmorIronShield", "IronArrow"]}
    k = P.kit_set(P.S("iron", ["IronSword"], "IronArrow", sh=True), vals)
    assert k["value"] == 60 and k["weapon_value"] == 10 and k["ammo"] == "Skyrim.esm:IronArrow"
    assert P.kit_set(P.S("iron", ["Missing"]), vals) is None
    assert P.kit_set(P.S("chitin-light", ["IronSword"]), {**vals, **{e: 1 for e in P.ARMOUR["chitin-light"]}})["items"][0].startswith("Dragonborn.esm:")


def test_every_kit_style_is_not_nordic_and_has_three_tiers():
    for style, tiers in P.KITS.items():
        assert set(tiers) == {"low", "mid", "high"} and all(len(v) >= 2 for v in tiers.values()), style
        for sets in tiers.values():
            for s in sets:
                assert not P.NORDIC.search(" ".join(P.ARMOUR[s["armour"]] + s["weapons"])), (style, s)


def act(band, size, kind="x", **kw):
    return {"band": band, "size": size, "kind": kind, "level": 5, "damage_bonus": T.bonus(size, band, BASE), **kw}


def test_damage_rises_with_band_and_d5_is_lethal_d1_is_not():
    assert [T.bonus("predator", b, BASE) for b in T.BAND_ORDER] == [0, 0, 0, 14, 35, 63]
    assert T.hit("giant", "D5", BASE) >= T.D5_LETHAL_HIT and T.hit("predator", "D5", BASE) < 100
    acts = {f"{b}{s}": act(b, s) for b in ("D1", "D2", "D3", "D5") for s in ("small", "game")}
    faults, doc = T.check(acts, {}, BASE, {"D2": [100], "D4": [500]})
    assert faults == [] and doc["peak_hit_by_band"]["D5"] > doc["peak_hit_by_band"]["D2"]


def test_toughness_faults():
    base = {"D1": act("D1", "predator")}
    assert any("D1 hostile" in f for f in T.check(base, {}, BASE, {})[0])                       # a D1 player-killer
    assert any("damage bonus" in f for f in T.check({"a": act("D3", "predator") | {"damage_bonus": 1}}, {}, BASE, {})[0])
    assert any("not fixed" in f for f in T.check({"a": act("D2", "small") | {"level_mult": True}}, {}, BASE, {})[0])
    assert any("not fixed" in f for f in T.check({"a": act("D2", "small") | {"template": "x"}}, {}, BASE, {})[0])
    assert any("weapon" in f for f in T.check({}, {}, BASE, {"D2": [500], "D4": [100]})[0])      # kit falling with the band


def test_committed_bindings_hold_the_variety_rules():
    groups = json.loads((REPO / "newworld/sources/ecology/bindings.json").read_text())["npc_groups"]
    bound = {k: g for k, g in groups.items() if g.get("records")}
    assert len(bound) >= 38 and len(groups) == 39
    for k, g in bound.items():
        assert len(set(g["looks"])) >= 4, k
        for v in (g.get("look_voices") or {}).values():
            assert not T.NORD_VOICE.search(v), k
        if g.get("gear_note"):
            continue
        means = {}
        for t, sets in g["gear"].items():
            assert len(sets) >= 2, (k, t)
            means[t] = sum(s["value"] for s in sets) / len(sets)
            for s in sets:
                assert not T.NORDIC_GEAR.search(" ".join(s.get("items", []) + s.get("weapons", []) + [s.get("outfit", "")])), (k, s)
        assert means["low"] < means["mid"] < means["high"], (k, means)
