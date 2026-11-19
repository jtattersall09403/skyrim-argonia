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
