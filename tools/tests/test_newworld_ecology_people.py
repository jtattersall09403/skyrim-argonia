"""Hostile people and toughness of the ecology stage (tools/newworld/ecology/people.py, toughness.py): looks are whole
non-Nord bandit-faction records, kit rises with the band's tier and is never Nordic, damage is the band's and the size
class's alone and rises with the band, and what is committed in bindings.json holds to the same rules."""
import json
from pathlib import Path

from tools.newworld.ecology import people as P
from tools.newworld.ecology import toughness as T

REPO = Path(__file__).resolve().parents[2]
BASE = {"blow_by_size": {"insect": 7.5, "small": 7.5, "game": 18.75, "predator": 52.5, "giant": 97.5}, "lowest": 7.5,
        "records": {"m:hard": {"unarmed": 40.0, "mult": 1.5}, "m:soft": {"unarmed": 5.0, "mult": 1.5}}}


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


def act(band, size, kind="x", src="m:hard", **kw):
    return {"band": band, "size": size, "kind": kind, "src": src, "level": 5,
            "damage_bonus": T.bonus(src, size, band, BASE), **kw}


def test_a_hard_hitting_record_is_brought_down_to_its_band():
    # the hackwing's own 60 (40 x 1.5) lands Skyrim's first animals' 7.5 in D1, a predator's band blow in D5
    assert T.bonus("m:hard", "predator", "D1", BASE) == -35 and T.hit("m:hard", "predator", "D1", BASE) == 7.5
    assert T.hit("m:hard", "predator", "D5", BASE) == 147.0 and T.bonus("m:soft", "small", "D2", BASE) == 0


def test_damage_rises_with_band_and_d5_is_lethal_d1_is_not():
    acts = {f"{b}{s}{r}": act(b, s, src=r) for b in ("D1", "D2", "D3", "D5") for s in ("small", "game") for r in ("m:hard", "m:soft")}
    faults, doc = T.check(acts, {}, BASE, {"D2": [100], "D4": [500]})
    assert faults == [] and doc["peak_hit_by_band"]["D5"] > doc["peak_hit_by_band"]["D2"]
    assert doc["peak_hit_by_band"]["D1"] <= T.D1_MAX_HIT


def test_toughness_faults():
    assert any("damage bonus" in f for f in T.check({"a": act("D1", "predator") | {"damage_bonus": 0}}, {}, BASE, {})[0])
    assert any("not measured" in f for f in T.check({"a": act("D2", "small", src="m:none")}, {}, BASE, {})[0])
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
