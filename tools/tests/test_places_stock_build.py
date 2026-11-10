"""What the build makes of a place's stock (tools/places/stock/plan.py) and what its check proves
(tools/places/stock/verify.py), on small fixtures with no game data."""
import copy
import sys
from pathlib import Path
from types import SimpleNamespace as NS

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import stock_fixture as SF  # noqa: E402

from tools.places.stock import plan as stockplan  # noqa: E402
from tools.places.stock import verify  # noqa: E402

LIST, CHEST, BASE_NPC, OUTFIT, FURS, TUNIC, BOOTS, FURS2 = ("Skyrim.esm:0A0001", "Skyrim.esm:0A0002", "Skyrim.esm:0A0003",
                                                           "Skyrim.esm:0A0004", "Skyrim.esm:0A0005", "Skyrim.esm:0A0006",
                                                           "Skyrim.esm:0A0007", "Skyrim.esm:0A0008")
ITEMS = {SF.GOLD: ("MISC", 1, (), 0), SF.DAGGER: ("WEAP", 10, ("WeapMaterialIron",), 0), SF.APPLE: ("ALCH", 3, (), 0),
         SF.RING: ("ARMO", 30, ("ArmorJewelry",), 0x40), SF.SCROLL: ("SCRL", 25, (), 0),
         FURS: ("ARMO", 50, ("ArmorLight",), 0x4), TUNIC: ("ARMO", 2, ("ArmorClothing",), 0x4),
         BOOTS: ("ARMO", 2, ("ArmorClothing",), 0x80), SF.SWORD: ("WEAP", 45, ("WeapMaterialSteel",), 0),
         FURS2: ("ARMO", 50, ("ArmorLight",), 0x8)}


class Rec:
    """The Records calls plan.py makes, over a few made-up records: a chest holding a levelled list (an apple at
    level 1, a dagger at 10), a person base with furs and a tunic and boots in a levelled outfit, carrying a dagger."""
    raw: dict = {}

    def sig(self, k):
        return {CHEST: "CONT", LIST: "LVLI", BASE_NPC: "NPC_"}.get(k) or (ITEMS[k][0] if k in ITEMS else None)

    def item(self, k):
        if k not in ITEMS:
            return None
        sig, value, kws, slots = ITEMS[k]
        return {"key": k, "sig": sig, "value": value, "keywords": list(kws), "ench": None, "slots": slots,
                "food": k == SF.APPLE, "edid": k, "name": k}

    def cont(self, k):
        return {"key": k, "edid": "CommonChest", "name": "Chest", "model": "", "items": [(LIST, 1), (SF.DAGGER, 1)],
                "respawns": True} if k == CHEST else None

    def lvli(self, k):
        return {"flags": 0, "entries": [(1, SF.APPLE, 2), (10, SF.DAGGER, 1)]} if k == LIST else None

    def fixed(self, k):
        return [(SF.APPLE, 2)] if k == LIST else [(k, 1)]

    def npc(self, k):
        return {"items": [(SF.DAGGER, 1)], "outfit": OUTFIT, "death_item": None} if k == BASE_NPC else None

    def outfit(self, k):
        return [FURS, TUNIC, BOOTS] if k == OUTFIT else []


def place():
    refs = [{"id": "X.esm:000009", "src": "X.esm:000009", "fk": "P:1", "space": "house", "base": CHEST, "kind": "container",
             "pos": [0, 0, 0]},
            {"id": "house/X.esm:00000A", "src": "X.esm:00000A", "fk": "P:2", "space": "house", "base": SF.SCROLL,
             "kind": "clutter", "pos": [0, 0, 0]},
            {"id": "house/X.esm:00000B", "src": "X.esm:00000B", "fk": "P:3", "space": "house", "base": SF.SCROLL,
             "kind": "clutter", "pos": [0, 0, 0]}]
    S = {"refs": refs, "by_id": {r["id"]: r for r in refs}}
    people = {"npcs": [{"id": "t.head", "fk": "P:10", "from": BASE_NPC, "edid": "ANP_t_head", "factions": []},
                       {"id": "t.guard", "fk": "P:11", "from": BASE_NPC, "edid": "ANP_t_guard", "factions": []}],
              "factions": [{"fk": "P:20", "name": "t town"}],
              "containers": [{"fk": "P:30", "edid": "chest", "from": "Skyrim.esm:0C644F", "who": "t.head"}]}
    row = NS(space_id="house", ref_id="X.esm:000009", owner_person_id=None, owner_household_id="t.household.house",
             owner_faction=None, lock_level_id="Novice", gold=30)
    st = NS(containers={("house", "X.esm:000009"): row},
            container_items={"X.esm:000009": [NS(item_id=SF.RING, count=1)]},
            loose={"X.esm:00000A": NS(id="X.esm:00000A", space_id="house", item_id=SF.SCROLL, count=1, owner_person_id=None,
                                      owner_faction="t.household.house", x=None, y=None, z=None, on_ref_id=None)},
            persons={"t.head": NS(id="t.head", household_id="t.household.house"),
                     "t.guard": NS(id="t.guard", household_id="t.household.house")},
            households={"t.household.house": NS(id="t.household.house")},
            person_items={"t.guard": [NS(item_id=SF.SWORD, count=1, worn=True), NS(item_id=SF.GOLD, count=5, worn=False),
                                      NS(item_id=FURS2, count=1, worn=True)]},
            traders={"t.head": NS(gold=500)}, trader_items={"t.head": [NS(item_id=SF.DAGGER, count=3)]},
            locks={"Novice": 1})
    return {"place": {"place_id": "t"}}, S, people, st


class Ids:
    def __init__(self):
        self.ids = {}

    def __call__(self, key):
        return self.ids.setdefault(key, f"P:{0x100 + len(self.ids):X}")


def run():
    P, S, people, st = place()
    problems, notes = [], []
    out = stockplan.plan(P, S, people, Ids(), problems.append, notes, st=st, rec=Rec())
    return out, S, people, problems


def test_a_stock_row_makes_a_container_of_ours_with_set_dressing_row_and_gold():
    out, S, people, problems = run()
    assert not problems, problems
    c = out["containers"][0]
    assert {(i["item"], i["count"]) for i in c["items"]} == {(SF.APPLE, 2), (SF.RING, 1), (SF.GOLD, 30)}  # never the dagger
    ref = S["by_id"]["X.esm:000009"]
    assert ref["base"] == c["fk"] and ref["lock"] == 1 and ref["owner"] == people["factions"][-1]["fk"]
    assert all({"faction": ref["owner"], "rank": 0} in n["factions"] for n in people["npcs"])  # the household's faction


def test_significant_loose_without_a_row_is_not_built_and_a_row_keeps_its_ref():
    out, S, _people, _ = run()
    assert "house/X.esm:00000B" not in S["by_id"] and "house/X.esm:00000A" in S["by_id"]
    assert out["kept_loose"] == ["X.esm:00000A"] and S["by_id"]["house/X.esm:00000A"]["count"] == 1


def test_people_carry_their_rows_and_wear_an_outfit_of_ours():
    out, _S, people, _ = run()
    guard = people["npcs"][1]
    assert guard["inventory"] == [{"item": SF.SWORD, "count": 1}, {"item": SF.GOLD, "count": 5}]  # the base's dagger goes
    outfit = next(o for o in out["outfits"] if o["fk"] == guard["outfit"])
    assert set(outfit["items"]) == {TUNIC, BOOTS, FURS2}       # the furs go; worn armour and set dressing in free slots
    head = people["npcs"][0]
    assert head["inventory"] == [] and next(o for o in out["outfits"] if o["fk"] == head["outfit"])["items"] == [TUNIC, BOOTS]


def test_a_trader_row_fills_the_merchant_chest():
    _out, _S, people, _ = run()
    assert people["containers"][0]["items"] == [{"item": SF.DAGGER, "count": 3}, {"item": SF.GOLD, "count": 500}]


def test_a_place_without_a_stock_source_is_built_as_before(monkeypatch):
    P, S, people, _st = place()
    monkeypatch.setattr(stockplan, "load_stock", lambda pid: None)
    assert stockplan.plan(P, S, people, Ids(), print, []) is None


def test_the_good_stock_passes():
    ctx = {"stock": SF.stock(), "plan": {"refs": []}}
    assert verify.check_stock(ctx) == [] and verify.check_promises(ctx) == []


BROKEN = {
    "untraced": lambda X: X["built"]["containers"][("house", "X.esm:000009")]["contents"].append((SF.DAGGER, 1)),
    "row not built": lambda X: X["built"]["loose"].clear(),
    "wrong owner": lambda X: X["built"]["containers"][("house", "X.esm:000009")].update(owner=None),
    "wrong lock": lambda X: X["built"]["containers"][("house", "X.esm:000009")].update(lock=25),
    "respawns": lambda X: X["built"]["containers"][("house", "X.esm:000009")].update(respawns=True),
    "over the tier": lambda X: X["containers"][0].update(tier="T3"),
    "over budget": lambda X: X["containers"][0]["items"].append((SF.SWORD, 3)),
    "never": lambda X: X["person_items"]["t.head"].append((SF.NORD, 1, False)),
    "ledger": lambda X: X["items"][SF.SWORD].update(tier="T6"),
    "above the band": lambda X: X["person_items"]["t.head"].append((SF.EBONY, 1, False)),
    "too much gold": lambda X: X["person_items"]["t.head"].append((SF.GOLD, 100, False)),
    "chest unlisted": lambda X: X["built"]["chests"]["t.head"]["contents"].append((SF.SWORD, 1)),
    "worn not built": lambda X: X["built"]["npcs"]["t.head"]["outfit_items"].clear(),
    "set dressing row not built": lambda X: X["containers"][0]["items"].append((SF.APPLE, 5)),
}


@pytest.mark.parametrize("name", list(BROKEN))
def test_each_broken_stock_fails(name):
    X = copy.deepcopy(SF.stock())
    BROKEN[name](X)
    assert verify.check_stock({"stock": X, "plan": {"refs": []}}), name


def test_an_open_promise_or_a_missing_map_marker_fails():
    X = SF.stock()
    X["deliveries"].append({"give_seq": 2, "kind": "treasure", "detail": "x", "status": "open", "by": "record",
                            "person": None, "ref": None, "why": "nothing delivers it"})
    assert verify.check_promises({"stock": X})
    X = SF.stock()
    X["world_markers"] = set()
    assert verify.check_promises({"stock": X})


def test_summary_counts_and_ranks():
    s = verify.summary(SF.stock())
    assert s["containers_authored"] == 1 and s["top"][0]["value"] == 45 and s["gold"] == 30 + 12 + 5


def test_the_scale_s_explicit_lists_win_over_value_everywhere_a_tier_is_computed():
    from tools.places.stock import split
    from tools.places.studio import stock as studio
    sc = split.scale()
    black = {"edid": "SoulGemBlack", "keywords": ["VendorItemSoulGem"], "value": 300}    # T3 by value alone
    grand = {"edid": "SoulGemGrand", "keywords": ["VendorItemSoulGem"], "value": 200}    # T2 by value alone
    assert split.item_tier(black, sc)[0] == "T6" and split.item_tier(grand, sc)[0] == "T5"
    assert studio._listed_tier(black, sc)[0] == "T6"                                     # the studio reads the same rule
    assert split.item_tier({"edid": "GemRuby", "keywords": ["VendorItemGem"], "value": 200}, sc)[0] == "T3"


def test_an_enchanted_thing_takes_its_enchantment_s_grade_and_an_unmeasured_one_stays_unknown():
    from tools.places.stock import split
    sc = split.scale()
    arcing = {"edid": "EnchIronSwordShock03", "keywords": ["WeapMaterialIron"], "value": 25, "ench": "Skyrim.esm:045F6F",
              "ench_grade": 3}
    assert split.item_tier(arcing, sc) == ("T3", "its enchantment's grade (3)")
    assert split.item_tier({**arcing, "ench": None, "ench_grade": None}, sc)[0] == "T1"
    assert split.item_tier({"edid": "Thing", "keywords": []}, sc) == (None, "")
    assert split.item_tier({"edid": "Thing", "keywords": [], "value": 260}, sc)[0] == "T3"
