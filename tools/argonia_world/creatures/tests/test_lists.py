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


def test_every_class_clears_skyrims_and_the_mods_kinds_bar():
    """Owner #37: never fewer kinds per equal-sized region than Skyrim.esm or Black Marsh.esm (data/ bars)."""
    w = db.open()
    r = checks.kind_bars(w)
    assert r["fail"] is None, r["fail"]
    assert r["classes"]["coastal-lagoon"]["kinds"] >= 14 and r["classes"]["northern-transition"]["kinds"] >= 18


def test_bar_follows_area():
    bars = {"skyrim": {"A": {"cells": 1500, "wild_kinds": 14}, "B": {"cells": 700, "wild_kinds": 18},
                       "C": {"cells": 150, "wild_kinds": 10}},
            "mod": {"M": {"cells": 1000, "wild_kinds": 26, "window_max": {"25": 14, "169": 23}}}, "mod_main": "M"}
    assert checks.bar_for(2000, bars)[::2] == (14, 26)
    assert checks.bar_for(160, bars)[::2] == (14, 23)  # never below the least-varied 600+ cell region
    assert checks.bar_for(700, bars)[0] == 18


def test_kept_animals_at_every_lived_in_settlement():
    w = db.open()
    lived = {r[0] for r in w.query("SELECT id FROM place WHERE classification_class = 'settlement' AND status IN "
                                   "('active', 'seasonal', 'contested')")}
    kept = {r[0] for r in w.query("SELECT home_place_id FROM npc WHERE id LIKE 'creature-at.%.domestic-%'")}
    assert "place.imperial-fringe.claywater-station" in kept and lived <= kept
    forms = {r[0] for r in w.query("SELECT creature_id FROM creature_form")}
    assert {"creature.guar", "creature.bantam-guar"} <= forms


def test_claywater_guar_stand_in_their_pen_with_a_sandbox():
    """Where the place is built the kept animals are actor REFRs with an owned pen marker (place_build's creature
    path: an NPC_ templated on the mod's guar that sandboxes around its pen all day)."""
    from tools.argonia_world import place_build as pb
    from tools.argonia_world.formids import Allocator
    w = db.open()
    refs = {r.id: r for r in w.rows("build_ref") if r.id.startswith("ref.claywater-station.kept-guar")}
    assert len(refs) == 4 and all(r.persistent for r in refs.values())
    cells = {c.id: c for c in w.rows("build_cell", place_id="place.imperial-fringe.claywater-station")}
    ctx = pb._Ctx(Allocator(w), w, None, None)
    pb._people(ctx, w, [r for r in w.rows("build_ref") if r.cell_id in cells], cells)
    g = ctx.records["ARG_Npc_DomesticGuar1"]
    assert g["template"] == "005BC9:King of the Murkmire.esp" and len(g["packages"]) == 1
