"""tools/newworld/consistency.py: one small broken fixture per check family, and its clean twin."""
from __future__ import annotations

import copy

from tools.newworld import consistency as C

TIERS = {"village": {"id": "village", "population_lo": 10, "population_hi": 30, "footprint_radius_m": 60.0},
         "town": {"id": "town", "population_lo": 30, "population_hi": 60, "footprint_radius_m": 110.0}}
SYMS = {"s.village": {"id": "s.village", "settlement_tier_id": "village"},
        "s.town": {"id": "s.town", "settlement_tier_id": "town"}}


def place(pid, name, sym="s.village", pop=20, kind="village", **kw):
    p = {"id": pid, "name": name, "symbol_id": sym, "place_kind_id": kind, "region_id": "r", "culture_id": "c",
         "cell_x": 0, "cell_y": 0, "px": 1, "py": 1, "on_water": False, "status": "inhabited", "held_by": "elders",
         "population": pop, "footprint_radius_m": 50.0, "siting": "inland", "importance": 1,
         "summary": f"{name} is a village."}
    p.update(kw)
    return p


def ctx(**over):
    P = {"a": place("a", "Alpha"), "b": place("b", "Beta", sym="s.town", pop=40, kind="town")}
    c = {"places": P, "place_ev": {k: f"place.jsonl:{i}" for i, k in enumerate(P, 1)},
         "notes": {"a": {"look": ("Huts on posts. A Hist stands at the centre.", "place_note.jsonl:1"),
                         "source": ("Its main source, Keeba (KotM), is a hamlet. Still to add: the pool of Hist sap.",
                                    "place_note.jsonl:2")},
                   "b": {"source": ("Its main source, Teeba (KotM), is a town, judged the closest match.", "place_note.jsonl:3")}},
         "gives": {"a": [{"place_id": "a", "seq": 0, "give_kind_id": "trader-general", "detail": "a stall", "_ev": "place_give.jsonl:1"}]},
         "danger": {"a": {"disposition_id": "friendly", "_ev": "d:1"}, "b": {"disposition_id": "friendly", "_ev": "d:2"}},
         "place_source": {"a": [{"rank": 0, "source_place_id": "s1", "why": "kind", "score": 0.8, "_ev": "ps:1"}],
                          "b": [{"rank": 0, "source_place_id": "s2", "why": "kind", "score": 0.8, "_ev": "ps:2"}]},
         "source_place": {"s1": {"id": "s1", "title": "Keeba (KotM)", "name": "Keeba", "culture_tags": "argonian"},
                          "s2": {"id": "s2", "title": "Teeba (KotM)", "name": "Teeba", "culture_tags": "argonian"}},
         "tiers": TIERS, "symbols": SYMS, "regions": {"r": {"name": "Reg"}}, "cultures": {"c": {"name": "Cul"}},
         "on_road": {"a", "b"}, "aliases": {}, "person_names": {"weeltul"}, "factions": {"faction.known"},
         "quests": [], "lines": {}, "drafts": {}, "main": {"b"}, "ground": {}, "map_page": None,
         "generated": {"digest": []}, "cell_region": {}}
    c.update(over)
    return c


def causes(c, fam):
    R = C.Report()
    C.FAMILIES[fam](c, R)
    return {f.cause for f in R.items}, R


def test_internal_clean_then_broken():
    assert causes(ctx(), "internal")[0] == set()
    c = ctx()
    c["danger"]["a"]["disposition_id"] = "hostile"
    c["gives"]["a"].append({"seq": 1, "give_kind_id": "combat-foes", "detail": "x", "_ev": "g:2"})
    c["places"]["b"]["population"] = 15
    got, R = causes(c, "internal")
    assert "a hostile or abandoned place offers a service" in got
    assert "population outside its settlement tier" in got
    assert "population out of order with its peers" in got
    assert all(f.evidence for f in R.items)
    c = ctx()
    c["gives"]["a"].append({"seq": 1, "give_kind_id": "combat-boss", "detail": "x", "_ev": "g:2"})
    assert "a friendly place gives a fight inside it" in causes(c, "internal")[0]


def test_ground_water_words_and_hist_sap():
    far = {"d": {"sea": 9000.0, "river": 9000.0, "lake": 9000.0, "swamp": 9000.0, "any": 9000.0}, "water": False, "ev": "px"}
    c = ctx(ground={"a": far, "b": far})
    assert causes(c, "ground")[0] == set()
    c["notes"]["a"]["look"] = ("Fishing boats tie up at the jetty. A Hist tree rises from a pool of clear water.", "n:1")
    c["places"]["a"]["on_water"] = True
    got, _ = causes(c, "ground")
    assert {"a water word with no such water on the ground", "on_water disagrees with the raster",
            "a Hist pool worded as water, not sap"} <= got


def test_source_note_against_source():
    assert causes(ctx(), "source")[0] == set()
    c = ctx()
    c["notes"]["a"]["source"] = ("Its main source, Gagroth Farm (JtBM), is a farm with four buildings.", "n:2")
    c["source_place"]["s1"]["culture_tags"] = "nordic"
    c["main"] = {"a", "b"}
    got, _ = causes(c, "source")
    assert {"the source note names another source than the allocated one",
            "a Nordic source whose note does not replace its Nordic pieces",
            "a main-quest place whose source is not judged"} <= got
    c = ctx()
    c["place_source"]["b"][0]["source_place_id"] = "s1"
    c["notes"]["b"]["source"] = ("Its main source, Keeba (KotM), is a hamlet, judged the closest match.", "n:3")
    assert "a shared source whose note does not say how this adaptation differs" in causes(c, "source")[0]


def test_atlas_against_record():
    page = {"a": {"n": "Alpha", "symid": "s.village", "reg": "r", "pop": 20, "radius": 50.0},
            "b": {"n": "Beta", "symid": "s.town", "reg": "r", "pop": 40, "radius": 50.0}}
    assert causes(ctx(map_page=page), "atlas")[0] == set()
    c = ctx(map_page=copy.deepcopy(page), cell_region={"0,0": "other"})
    c["map_page"]["a"]["pop"] = 3
    c["on_road"] = set()
    c["places"]["b"]["footprint_radius_m"] = 500.0
    got, _ = causes(c, "atlas")
    assert {"the map page is behind the records", "the record's region differs from its cell's",
            "a town or city on no road", "the footprint is too big for its tier"} <= got


def test_story_against_records():
    q = {"id": "quest.main.mn99", "settlement": "a", "touches": [{"id": "faction.ghost", "access": "read"}],
         "cast": [{"id": "npc.x", "persona": {"status": "canon", "name": "Nobody-Here", "home": "a (the hut)"}}],
         "placements": [{"ref": "thing.x", "anchor": {"place": "a", "need": "on the quay by the market"}},
                        {"ref": "thing.y", "anchor": {"place": "zz-ruin-1-m2"}}]}
    text = "id: quest.main.mn99\nfaction.ghost\nNobody-Here\nref: thing.x\non the quay by the market\nzz-ruin-1-m2\n"
    c = ctx(quests=[{"path": "newworld/story/quests/main/mn99.yaml", "text": text, "data": q}])
    got, R = causes(c, "story")
    assert "a quest names a faction not in the records" in got
    assert "a quest names a person not in the records" in got
    assert "a quest names a place not in the records" in got
    assert "a quest placement with no spot in its place's quests.jsonl" in got
    assert any(c.startswith("a quest asks of a place what its record and draft lack") for c in got)
    assert all("mn99.yaml:" in f.evidence for f in R.items)
    q2 = {"id": "quest.side.s1", "settlement": "a"}
    assert causes(ctx(quests=[{"path": "newworld/story/quests/side/s1.yaml", "text": "", "data": q2}]), "story")[0] == set()


def test_drafts():
    d = {"place": {"draft": {"plan": {"gives": {"0": "the stall"}, "look": {"0": "posts", "1": "the tree"},
                                      "structures": {"hall": {"verdict": "keep"}}}}},
         "rel": "newworld/places/a/place.json", "people": 20, "spaces": [], "spots": set(),
         "check": {"results": {"nordic": {"ok": True}, "seat": {"ok": True}}}, "check_newer": True}
    assert causes(ctx(drafts={"a": d}), "draft")[0] == set()
    bad = copy.deepcopy(d)
    bad["place"]["draft"]["plan"] = {"gives": {}, "look": {"0": "x"}, "structures": {"hall": {}}}
    bad["people"] = 3
    bad["check"]["results"]["nordic"] = {"ok": False, "n": 1, "failures": ["NorHouse01"]}
    bad["check_newer"] = False
    got, _ = causes(ctx(drafts={"a": bad}), "draft")
    assert {"the plan misses a gives row", "the plan misses a look sentence", "a major structure without a verdict",
            "the draft's people differ from the population", "a Nordic piece in the draft",
            "the built check is older than the draft"} <= got
    nop = copy.deepcopy(d)
    nop["place"]["draft"] = {}
    assert "a draft with no plan" in causes(ctx(drafts={"a": nop}), "draft")[0]


def test_generated():
    assert causes(ctx(), "generated")[0] == set()
    c = ctx(generated={"atlas": "Atlas behind", "explorer": None, "digest": ["story/design/world/province.md"]})
    assert causes(c, "generated")[0] == {"the Atlas is behind its sources", "the story digest is behind its sources"}


def test_counts_group_by_family_and_cause():
    R = C.Report()
    R.add("internal", "x", "a", "w", "e")
    R.add("internal", "x", "b", "w", "e")
    assert C.counts(R) == {"internal: x": 2}
    assert "## internal: x  (2, baseline 1)" in C.render(R, {"internal: x": 1})
