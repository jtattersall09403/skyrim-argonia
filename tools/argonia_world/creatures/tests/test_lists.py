"""The derived lists (L1, owner play test 3 finding 13): the quiet bands' prey lives on in the dangerous bands' lists,
no apex kind is in a list, every class's lists hold MIN_KINDS kinds, and density meets vanilla's on synthetic refs."""
import numpy as np

from tools.argonia_world import db
from tools.argonia_world.creatures import checks


def _kinds(w, lid):
    return {r["creature_id"] for r in w.query("SELECT f.creature_id FROM creature_list_entry e JOIN creature_form f "
                                              "USING (form_key) WHERE e.list_id = ?", lid)}


def test_lists_are_cumulative_and_apex_free():
    w = db.open()
    assert checks.lists(w)["fail"] is None
    d1, d3 = _kinds(w, "lvln.coastal-lagoon.D1.land"), _kinds(w, "lvln.coastal-lagoon.D3.land")
    assert d1 <= d3 and "creature.hackwing" in d3 and len(d3) >= 4  # before: hackwing and fleshfly alone


def test_terrain_class_matches_vanilla_cuts():
    flat = np.zeros((33, 33))
    assert checks.terrain_class(flat - 1, 0.0, 0) == "water"
    h = flat + 1
    h[0, 0] = -1
    assert checks.terrain_class(h, 0.0, 0) == "shore"
    assert checks.terrain_class(flat + 60, 0.0, 0) == "mountain"
    assert checks.terrain_class(flat + 1, 0.0, 10) == "forest"
    assert checks.terrain_class(flat + 1, 0.0, 9) == "open"
