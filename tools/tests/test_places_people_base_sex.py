"""draft people: a person's actor base honours their identity's sex and race, and the draft refuses (never picks the
other sex) when the pool has no base of that sex."""
import pytest

from tools.places.draft import people


def npc(key, sex, race="ArgonianRace", edid="Townsfolk"):
    return {"key": key, "edid": f"{edid}{key}", "sex": sex, "race_edid": race, "factions": [], "type": "NPC_"}


NPCS = {k: npc(k, s, r) for k, s, r in (("m1", "male", "ArgonianRace"), ("f1", "female", "ArgonianRace"),
                                         ("f2", "female", "DarkElfRace"))}
POOL = [("exterior", {"base": k, "kind": "actor"}) for k in NPCS]


def test_the_base_follows_the_identitys_sex_and_race():
    pick = people.base_picker(POOL, NPCS)
    assert pick("resident", {"sex": "male"}) == "m1"
    assert pick("resident", {"sex": "female", "race": "DarkElfRace"}) == "f2"
    assert pick("resident", {"sex": "female", "race": "ArgonianRace"}) == "f1"
    assert pick("resident", {"sex": "female", "race": "KhajiitRace"}) in ("f1", "f2")   # no such race: sex still holds


def test_rebase_moves_a_person_built_on_the_other_sex():
    folk = [{"id": "p1", "role": "resident", "base_from": "m1"}, {"id": "p2", "role": "resident", "base_from": "m1"}]
    who = {"p1": {"sex": "female", "race": "ArgonianRace"}, "p2": {"sex": "male"}}
    assert people.rebase(folk, {}, POOL, NPCS, who) == ["p1"]
    assert [p["base_from"] for p in folk] == ["f1", "m1"]


def test_no_base_of_the_sex_refuses_with_the_person_named():
    only_men = {"m1": NPCS["m1"]}
    folk = [{"id": "camp.p3", "role": "resident", "base_from": None}]
    with pytest.raises(people.NoBase, match=r"camp\.p3: the identity is female.*male only"):
        people.rebase(folk, {}, [("exterior", {"base": "m1"})], only_men, {"camp.p3": {"sex": "female"}})
