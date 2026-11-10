"""Danger: the cell rules, each place's disposition, strength, reach and reward, and the wealth derived from them
(tools/newworld/danger.py, place_danger.py, wealth.py; docs/design/danger.md)."""
import json
from types import SimpleNamespace as NS

import pytest

from tools.argonia_world import db
from tools.newworld import frame as f
from tools.newworld import place_danger as pd
from tools.newworld import wealth


@pytest.fixture(scope="module")
def world():
    return db.open(f.ROOT)


def test_the_built_world_keeps_the_invariants(world):
    assert pd.problems(world) == []


def test_place_wealth_is_derived_from_the_current_reward_bands(world):
    on_file = {r["id"]: {k: v for k, v in r.items() if k != "owner"}
               for r in json.loads(wealth.WEALTH.read_text())["places"]}
    stale = [r["id"] for r in wealth.derive(world) if on_file.get(r["id"]) != r]
    assert stale == [], f"rerun python3 -m tools.newworld.wealth derive: {stale[:5]}"


@pytest.mark.parametrize("disp, danger_tier, wealth_tier, want", [
    ("friendly", "T5", "T1", "T1"),      # a tree-minder's post in lethal country holds a tree-minder's goods
    ("wary", "T4", "T2", "T2"),
    ("friendly", "T1", "T4", "T4"),      # a city: its wealth, whatever its safe ground
    ("hostile", "T4", "T1", "T4"),       # an occupied place: what the fight guards
])
def test_a_lived_places_ceiling_is_whose_goods_they_are(disp, danger_tier, wealth_tier, want):
    rank = {f"T{i}": i for i in range(1, 6)}
    top, why = wealth.ceiling_of(disp, danger_tier, wealth_tier, rank)
    assert top == want and why


def test_reach_is_the_worst_band_on_the_calmest_way(world):
    class W:
        def rows(self, t, **k):
            return {"place": [NS(id="s", name="S", cell_x=0, cell_y=0)],
                    "travel_stop": [NS(place_id="s", travel_mode_id="boat")], "road": []}[t]
    cells = {(0, 0): "D1", (1, 0): "D4", (1, 1): "D2", (2, 1): "D2", (2, 0): "D3", (3, 0): "D5"}
    r = pd.reach(W(), cells)
    assert r[(2, 0)][0] == "D3"          # round the D4 cell through D2, then into its own D3
    assert r[(3, 0)][0] == "D5"          # its own cell counts
    assert r[(1, 0)][0] == "D4"


@pytest.mark.parametrize("kind, disp, gives, research, want", [
    ("town", "friendly", [], "D1", "D0"),                                          # safe inside, whatever surrounds
    ("hamlet", "friendly", [], "D1", "D4"),                                        # people of deadly country
    ("velothi-ruin", "abandoned", [NS(give_kind_id="combat-boss", setting=None, detail="a wraith")], None, "D5"),
    ("shipwreck", "abandoned", [NS(give_kind_id="combat-creature", setting=None, detail="mudcrabs")], None, "D4"),
    ("cave", "hostile", [NS(give_kind_id="combat-foes", setting=None, detail="smugglers")], None, "D5"),
    ("tribal-camp", "hostile", [NS(give_kind_id="combat-foes", setting=None, detail="raiders")], "D5", "D5"),
])
def test_strength_follows_the_rules(kind, disp, gives, research, want):
    kinds = {"town": "buildings", "hamlet": "buildings", "velothi-ruin": "dungeon", "shipwreck": "underwater",
             "cave": "cave", "tribal-camp": "none"}
    p = NS(place_kind_id=kind, danger_band_id=research)
    b, why = pd.strength(p, NS(interior=kinds[kind]), disp, gives, "D4", "deep")
    assert b == want and why


def test_an_encounter_stands_where_its_bearing_and_distance_put_it():
    p = NS(world_x=f.CELL_UNITS * 0.5, world_y=f.CELL_UNITS * 0.5)
    north = NS(bearing_deg=0, distance_m=f.CELL_UNITS / f.UNITS_PER_METRE)        # one cell's width north
    east = NS(bearing_deg=90, distance_m=f.CELL_UNITS / f.UNITS_PER_METRE)
    assert pd.spot_cell(p, north) == (0, 1)
    assert pd.spot_cell(p, east) == (1, 0)


def test_every_encounter_is_at_least_the_ground_it_stands_on(world):
    cells = {(c.x, c.y): c.danger_band_id for c in world.rows("cell")}
    rows = world.rows("place_encounter")
    assert rows, "the restored encounters (issue #60, ruling A) are in the database"
    for e in rows:
        assert pd.RANK[e.strength_band_id] >= pd.RANK[cells[(e.cell_x, e.cell_y)]]
        assert pd.RANK[e.reward_band_id] >= pd.RANK[e.strength_band_id]
