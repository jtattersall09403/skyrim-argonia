"""What a place gives: the give kinds lookup and build_db's checks on a place record's gives list."""
import pytest

from tools.newworld.build_db import REWARD_FOR, load_give_kinds, place_gives

KINDS = {k["id"]: k for k in load_give_kinds()}


def test_give_kinds_are_complete_and_grouped():
    groups = {k["group"] for k in KINDS.values()}
    assert groups == {"travel", "trade", "craft", "train", "rest", "blessing", "resource", "loot", "combat"}
    for k in KINDS.values():
        assert k["name"] and k["delivers"] and k["evidence"], k["id"]
    combat = {i for i, k in KINDS.items() if k["group"] == "combat"}
    assert combat == set(REWARD_FOR)
    assert all(KINDS[r]["group"] == "loot" for rs in REWARD_FOR.values() for r in rs)


def test_a_record_without_gives_builds_to_no_rows():
    assert place_gives("p", {}, KINDS) == []
    assert place_gives("p", {"gives": []}, KINDS) == []


def test_gives_become_rows_in_order_with_their_reward():
    r = {"gives": [{"kind": "trainer", "detail": "Expert Alteration trainer"},
                   {"kind": "ore-vein", "detail": "iron and corundum veins", "count": 3},
                   {"kind": "combat-boss", "detail": "the pirate captain", "reward": "boss-chest"},
                   {"kind": "boss-chest", "detail": "boss chest, D3 tier"}]}
    rows = place_gives("p", r, KINDS)
    assert [(x["seq"], x["give_kind_id"], x["count"], x["reward_kind_id"]) for x in rows] == [
        (0, "trainer", 1, None), (1, "ore-vein", 3, None), (2, "combat-boss", 1, "boss-chest"), (3, "boss-chest", 1, None)]


@pytest.mark.parametrize("gives, msg", [
    ([{"kind": "teleporter", "detail": "x"}], "unknown kind"),
    ([{"kind": "forge", "detail": " "}], "no detail"),
    ([{"kind": "combat-foes", "detail": "bandits"}], "reward must be"),
    ([{"kind": "combat-foes", "detail": "bandits", "reward": "trainer"}], "reward must be"),
    ([{"kind": "combat-boss", "detail": "chief", "reward": "treasure"}, {"kind": "treasure", "detail": "x"}], "reward must be"),
    ([{"kind": "combat-foes", "detail": "bandits", "reward": "boss-chest"}], "not among"),
    ([{"kind": "forge", "detail": "a forge", "reward": "boss-chest"}], "only a combat give"),
    ([{"kind": "forge", "detail": "a forge", "count": 0}], "at least 1"),
])
def test_bad_gives_are_rejected(gives, msg):
    with pytest.raises(ValueError, match=msg):
        place_gives("p", {"gives": gives}, KINDS)
