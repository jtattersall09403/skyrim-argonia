"""Place records keep their researched population and fit the ground (decision 0040)."""
import glob
import json
from pathlib import Path

from tools.newworld import build_db
from tools.newworld import record_check as rc

ROOT = Path(__file__).resolve().parents[2]
TIERS = {"settlement.outpost": ("outpost", 2, 12, False), "settlement.village": ("village", 5, 15, False),
         "settlement.town-seat": ("town", 12, 30, True)}
NEAR = {"sea": 3000.0, "river": 900.0, "lake": 50.0, "swamp": 10.0, "any": 10.0}


def place(pid, sym, pop, status="inhabited"):
    return {"id": pid, "symbol_id": sym, "population": pop, "status": status}


def test_population_outside_the_tier_is_a_fault():
    faults = rc.population_faults([place("a", "settlement.outpost", 15)], TIERS)
    assert [p for p, _ in faults] == ["a"]


def test_a_seat_may_run_a_quarter_over():
    assert rc.population_faults([place("a", "settlement.town-seat", 36)], TIERS) == []


def test_tiers_keep_their_order():
    faults = rc.population_faults([place("o", "settlement.outpost", 10), place("v", "settlement.village", 8)], TIERS)
    assert faults and faults[0][0] == "v"
    assert rc.population_faults([place("o", "settlement.outpost", 8), place("v", "settlement.village", 8)], TIERS) == []


def test_a_ruin_is_not_held_to_a_tier():
    assert rc.population_faults([place("r", "settlement.village", 0, "ruined")], TIERS) == []


def test_water_words_need_water_in_reach():
    assert rc.water_faults({"overview": "It sits on the river below the fort."}, None, NEAR)
    assert rc.water_faults({"overview": "It sits on the lake below the fort."}, "lakeshore", NEAR) == []
    assert rc.water_faults({"history": "Its founders came down a river far away."}, None, NEAR) == []


def test_siting_needs_its_water():
    assert rc.water_faults({}, "riverbank", NEAR)
    assert rc.water_faults({}, "swamp", NEAR) == []


def test_a_hist_pool_is_sap():
    assert rc.hist_faults({"faith": "A Hist tree stands in a pool at the heart of the town."})
    assert rc.hist_faults({"faith": "A Hist tree rises from a pool of its own sap."}) == []


def test_water_pixel_is_the_pixel_the_point_lies_in():
    assert build_db.water_pixel(1789.9, 2124.2) == (1789, 2124)


def test_the_database_keeps_each_record_s_population():
    """build_db writes the research estimate; a source's people count never replaces it."""
    research = {r["id"]: r["population"] for fn in glob.glob(str(ROOT / "newworld/sources/research/places/*.json"))
                for r in json.loads(Path(fn).read_text())["records"]}
    built = {p["id"]: p["population"] for p in
             (json.loads(line) for line in (ROOT / "newworld/story/data/db/place.jsonl").read_text().splitlines()
              if line.strip())}
    assert {k: v for k, v in built.items() if research.get(k) != v} == {}
    assert not hasattr(build_db, "source_match_population")


def give(kind, reward=None, detail="x"):
    return {"give_kind_id": kind, "detail": detail, "reward_kind_id": reward}


def test_a_friendly_village_gives_no_fight_against_people():
    gs = [give("combat-foes", "treasure"), give("treasure"), give("combat-creature", "treasure")]
    faults = rc.gives_faults("village", "friendly", 9, gs, "")
    assert len(faults) == 1 and "combat-foes" in faults[0]


def test_a_dead_place_offers_no_service():
    assert rc.gives_faults("keep", "hostile", 6, [give("fence")], "")
    assert rc.gives_faults("ruin", "abandoned", 0, [give("free-bed")], "")
    assert rc.gives_faults("village", "friendly", 9, [give("fence")], "") == []


def test_a_second_store_is_a_fight_s_reward():
    rewarded = [give("combat-foes", "treasure"), give("combat-boss", "boss-chest"), give("treasure"), give("boss-chest")]
    assert rc.gives_faults("cave", "hostile", 0, rewarded, "") == []
    loose = [give("combat-boss", "boss-chest"), give("boss-chest"), give("gold-hoard")]
    assert "gold-hoard" in rc.gives_faults("cave", "hostile", 0, loose, "")[0]
    assert rc.gives_faults("shipwreck", "abandoned", 0, [give("treasure")], "") == []


def test_a_trade_needs_people_and_a_vein_a_mine():
    assert rc.gives_faults("camp", "wary", 1, [give("trader-general")], "")
    assert rc.gives_faults("village", "friendly", 9, [give("ore-vein")], "clay on the shore")
    assert rc.gives_faults("village", "friendly", 9, [give("ore-vein")], "the old clay pits") == []
    assert rc.gives_faults("mine", "hostile", 0, [give("ore-vein")], "") == []


def test_the_database_keeps_the_gives_rules():
    rows = lambda n: [json.loads(line) for line in (ROOT / f"newworld/story/data/db/{n}.jsonl").read_text().splitlines()
                      if line.strip()]
    disp = {r["place_id"]: r["disposition_id"] for r in rows("place_danger")}
    gives, text = {}, {}
    for g in rows("place_give"):
        gives.setdefault(g["place_id"], []).append(give(g["give_kind_id"], g.get("reward_kind_id"), g["detail"] or ""))
    for n in rows("place_note"):
        text[n["place_id"]] = text.get(n["place_id"], "") + " " + n["text"]
    bad = [(p["id"], m) for p in rows("place")
           for m in rc.gives_faults(p["place_kind_id"], disp.get(p["id"], ""), p["population"], gives.get(p["id"], []),
                                    (p["summary"] or "") + text.get(p["id"], ""))]
    assert bad == []
