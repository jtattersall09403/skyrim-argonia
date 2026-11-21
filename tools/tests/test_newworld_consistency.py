"""tools/newworld/consistency.py: one small broken fixture per check family, and its clean twin."""
from __future__ import annotations

import copy

from tools.newworld import consistency as C

TIERS = {"village": {"id": "village", "population_lo": 10, "population_hi": 30, "footprint_radius_m": 60.0},
         "town": {"id": "town", "population_lo": 30, "population_hi": 60, "footprint_radius_m": 110.0},
         "outpost": {"id": "outpost", "population_lo": 2, "population_hi": 25, "footprint_radius_m": 40.0}}
SYMS = {"s.village": {"id": "s.village", "settlement_tier_id": "village"},
        "s.town": {"id": "s.town", "settlement_tier_id": "town"},
        "s.outpost": {"id": "s.outpost", "settlement_tier_id": "outpost"},
        "s.camp": {"id": "s.camp"}}


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
         "on_road": {"a", "b"}, "on_route": set(), "aliases": {}, "person_names": {"weeltul"}, "factions": {"faction.known"},
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


def test_peers_compare_true_settlements_only():
    c = ctx()
    c["places"]["o"] = place("o", "Outpost", sym="s.outpost", pop=24, kind="outpost")
    c["places"]["k"] = place("k", "Camp", sym="s.camp", pop=40, kind="tribal-camp")
    assert causes(c, "internal")[0] == set()  # an outpost or a camp outnumbering a village is no fault
    c["places"]["b"]["population"] = 15  # a town below a village is
    assert "population out of order with its peers" in causes(c, "internal")[0]


def test_a_second_store_needs_a_fight_that_rewards_it():
    def g(kind, reward=None):
        return {"give_kind_id": kind, "detail": "x", "reward_kind_id": reward, "_ev": "g:9"}
    c = ctx()
    c["danger"]["a"]["disposition_id"] = "hostile"
    c["gives"]["a"] = [g("combat-creature", "treasure"), g("combat-boss", "boss-chest"), g("treasure"), g("boss-chest")]
    assert "more than one treasure" not in causes(c, "internal")[0]
    c["gives"]["a"] = [g("combat-boss", "boss-chest"), g("boss-chest"), g("gold-hoard")]
    got, R = causes(c, "internal")
    assert "more than one treasure" in got and any("gold-hoard" in f.what for f in R.items)
    c["gives"]["a"] = [g("treasure")]
    assert "more than one treasure" not in causes(c, "internal")[0]


def test_ground_water_words_and_hist_sap():
    far = {"d": {"sea": 9000.0, "river": 9000.0, "lake": 9000.0, "swamp": 9000.0, "any": 9000.0}, "water": False, "ev": "px"}
    c = ctx(ground={"a": far, "b": far})
    assert causes(c, "ground")[0] == set()
    c["notes"]["a"]["look"] = ("Fishing boats tie up at the jetty. A Hist tree rises from a pool of clear water.", "n:1")
    c["places"]["a"]["on_water"] = True
    got, _ = causes(c, "ground")
    assert {"a water word with no such water on the ground", "on_water disagrees with the raster",
            "a Hist pool worded as water, not sap"} <= got
    c = ctx(ground={"a": far, "b": far})
    c["places"]["a"]["summary"] = "A town built over the Ayleid ruin of Silyanorn."
    c["notes"]["a"]["source"] = ("The marsh comes from the pool: Hist roots and bog beacons.", "n:2")
    assert causes(c, "ground")[0] == set()  # "built over" a ruin; the source note's asset pool
    c["places"]["a"]["summary"] = "A port built over shallow water."
    c["notes"]["a"]["look"] = ("A Hist stands in the square's pond.", "n:1")
    got, _ = causes(c, "ground")
    assert {"a water word with no such water on the ground", "a Hist pool worded as water, not sap"} <= got


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
    got, R = causes(c, "atlas")
    assert {"the map page is behind the records", "the record's region differs from its cell's",
            "a town or city on no road or travel route", "the footprint is too big for its tier"} <= got
    assert {f.place for f in R.items if f.cause.startswith("a town or city")} == {"b"}  # a village needs no road


def test_a_town_is_reached_by_road_or_route_and_a_keep_is_no_town():
    c = ctx(on_road=set(), on_route={"b"})
    assert "a town or city on no road or travel route" not in causes(c, "atlas")[0]
    c = ctx(on_road=set())
    c["places"]["b"].update(symbol_id="s.outpost", place_kind_id="keep", population=20, importance=4)
    assert "a town or city on no road or travel route" not in causes(c, "atlas")[0]


def test_story_against_records():
    q = {"id": "quest.main.mn99", "settlement": "a", "touches": [{"id": "faction.ghost", "access": "read"}],
         "cast": [{"id": "npc.x", "persona": {"status": "canon", "name": "Nobody-Here", "home": "a (the hut)"}}],
         "placements": [{"ref": "thing.x", "anchor": {"place": "a", "need": "on the quay by the market"}},
                        {"ref": "thing.y", "anchor": {"place": "zz-ruin-1-m2"}}]}
    text = "id: quest.main.mn99\nfaction.ghost\nNobody-Here\nref: thing.x\non the quay by the market\nzz-ruin-1-m2\n"
    drafted = {"a": {"place": {}, "rel": "newworld/places/a/place.json", "people": 20, "spaces": [], "spots": set(),
                     "check": None, "check_newer": True}}
    c = ctx(quests=[{"path": "newworld/story/quests/main/mn99.yaml", "text": text, "data": q}], drafts=drafted)
    got, R = causes(c, "story")
    assert "a quest names a faction not in the records" in got
    assert "a quest names a person not in the records" in got
    assert "a quest names a place not in the records" in got
    assert "a quest placement with no spot in its place's quests.jsonl" in got
    assert any(c.startswith("a quest asks of a place what its record and draft lack") for c in got)
    assert all("mn99.yaml:" in f.evidence for f in R.items)
    undrafted = ctx(quests=[{"path": "newworld/story/quests/main/mn99.yaml", "text": text, "data": q}])
    assert "a quest placement with no spot in its place's quests.jsonl" not in causes(undrafted, "story")[0]
    spotted = copy.deepcopy(drafted)
    spotted["a"]["spots"] = {"quest.main.mn99/thing.x"}
    c = ctx(quests=[{"path": "newworld/story/quests/main/mn99.yaml", "text": text, "data": q}], drafts=spotted)
    assert "a quest placement with no spot in its place's quests.jsonl" not in causes(c, "story")[0]
    cast = copy.deepcopy(drafted)
    cast["a"]["spots"] = cast["a"]["spots"] | {"cast/thing.x"}  # a person of the place's people source cast as the placement's ref
    c = ctx(quests=[{"path": "newworld/story/quests/main/mn99.yaml", "text": text, "data": q}], drafts=cast)
    assert "a quest placement with no spot in its place's quests.jsonl" not in causes(c, "story")[0]
    q2 = {"id": "quest.side.s1", "settlement": "a"}
    assert causes(ctx(quests=[{"path": "newworld/story/quests/side/s1.yaml", "text": "", "data": q2}]), "story")[0] == set()


def test_drafts():
    d = {"place": {"draft": {"plan": {"gives": [{"kind": "trader-general", "by": "the stall"}],
                                      "look": [{"line": "posts", "by": "posts"}],
                                      "structures": [{"structure": "walls", "what": "hall", "verdict": "kept",
                                                      "why": "the record's hall"}]}}},
         "rel": "newworld/places/a/place.json", "people": 20, "spaces": [], "spots": set(),
         "check": {"results": {"nordic": {"ok": True}, "seat": {"ok": True}}}, "check_newer": True}
    assert causes(ctx(drafts={"a": d}), "draft")[0] == set()
    bad = copy.deepcopy(d)
    bad["place"]["draft"]["plan"] = {"look": [{"line": "x", "by": ""}], "structures": [{"what": "hall", "why": "?"}]}
    bad["people"] = 3
    bad["check"]["results"]["nordic"] = {"ok": False, "n": 1, "failures": ["NorHouse01"]}
    bad["check_newer"] = False
    got, _ = causes(ctx(drafts={"a": bad}), "draft")
    assert {"the plan misses a gives row", "a plan line delivered by nothing", "a major structure without a verdict",
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
    assert "## internal: x  (2)" in C.render(R)


def test_a_finding_fails_the_run(monkeypatch, capsys):
    monkeypatch.setattr(C, "load", lambda: ctx())
    assert C.main(["--family", "internal"]) == 0
    broken = ctx()
    broken["places"]["b"]["population"] = 5
    monkeypatch.setattr(C, "load", lambda: broken)
    assert C.main(["--family", "internal"]) == 1
    assert not hasattr(C, "BASELINE")


def test_a_draft_of_another_source_fails_unless_marked_awaiting_its_redraft():
    d = {"place": {"source_id": "s1", "draft": {"plan": {"gives": [{"kind": "trader-general", "by": "the stall"}]}}},
         "rel": "newworld/places/a/place.json", "people": 20, "spaces": [], "spots": set(),
         "check": {"results": {}}, "check_newer": True}
    assert "a draft from another source than its allocated one" not in causes(ctx(drafts={"a": d}), "draft")[0]
    old = copy.deepcopy(d)
    old["place"]["source_id"] = "s9"
    assert "a draft from another source than its allocated one" in causes(ctx(drafts={"a": old}), "draft")[0]
    old["place"]["redraft"] = {"source_id": "s1", "why": "source changed to s1 2026-11-21; drafted from s9"}
    got, R = causes(ctx(drafts={"a": old}), "draft")
    assert not {c for c in got if "source" in c or "redraft" in c}
    assert [f.cause for f in R.owed] == ["a draft awaiting its redraft from a new source"]
    old["place"]["redraft"] = {"source_id": "s7", "why": "source changed to s7 2026-11-21 by hand"}
    assert "a redraft mark naming another source than the allocated one" in causes(ctx(drafts={"a": old}), "draft")[0]
    d["place"]["redraft"] = {"source_id": "s1", "why": "source changed to s1 2026-11-21 by hand"}
    assert "a redraft mark on a draft already of its source" in causes(ctx(drafts={"a": d}), "draft")[0]
