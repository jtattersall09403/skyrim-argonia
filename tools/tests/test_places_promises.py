"""The promise list (tools/places/promises.py) and the quest states (tools/places/states.py): gathering every
sentence that promises something of a place, the check that each has a row with built evidence, and each state's
refs as the game shows them."""
import json
from pathlib import Path

import pytest

from tools.places import promises as P
from tools.places import states as S

ROOT = Path(__file__).resolve().parents[2]


def jl(p: Path, rows):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("".join(json.dumps(r) + "\n" for r in rows))


@pytest.fixture
def world(tmp_path):
    db, quests, places = tmp_path / "db", tmp_path / "quests", tmp_path / "places"
    jl(db / "place.jsonl", [{"id": "weir", "name": "Teel-Fen Weir"}])
    jl(db / "place_alias.jsonl", [])
    jl(db / "place_note.jsonl", [
        {"place_id": "weir", "aspect_id": "faith", "text": "The wardens hatch their eggs in the sap pool. They are pious."},
        {"place_id": "weir", "aspect_id": "climate", "text": "Hot and wet, with a sap pool of rain."},
        {"place_id": "other", "aspect_id": "look", "text": "A tent on a platform."}])
    jl(db / "place_give.jsonl", [{"place_id": "weir", "seq": 0, "give_kind_id": "cooking-pot", "detail": "by the rack"}])
    jl(db / "place_need.jsonl", [{"place_id": "weir", "seq": 2, "thing": "the same Hist dead and blackened"}])
    jl(db / "place_need_sign.jsonl", [])
    jl(db / "person.jsonl", [{"id": "weir.P1", "name": "Paa-shei", "place_id": "weir", "trade": "cook at the pot"}])
    jl(db / "person_note.jsonl", [{"person_id": "weir.P1", "aspect_id": "backstory",
                                   "text": "She cooks eels in the pot each morning. She is kind."}])
    jl(db / "trader.jsonl", [])
    quests.mkdir()
    (quests / "main").mkdir(parents=True)
    (quests / "main" / "q1.yaml").write_text(json.dumps({
        "id": "quest.q1", "code": "Q1",
        "placements": [{"ref": "npc.q1.keeper", "kind": "person", "name": "Keeper",
                        "anchor": {"place": "weir", "need": "asleep in the hut at night"}},
                       {"ref": "thing.q1.key", "kind": "thing", "carriedBy": "npc.q1.keeper",
                        "anchor": {"place": "weir", "need": "on his belt"}}],
        "things": [{"id": "thing.q1.dead", "kind": "static", "source": "a dead Hist switched on at Teel-Fen Weir"}],
        "stages": [{"id": 10, "place": "weir", "journalText": "I should find the keeper in his hut. It is late."},
                   {"id": 20, "place": "elsewhere", "journalText": "Teel-Fen Weir lies south. I rest here."}],
        "endings": [{"id": "e1", "seen": "the tree at Teel-Fen Weir dead and the camp empty",
                     "world": [{"disableRef": "npc.q1.keeper"}]}]}))
    pd = places / "weir"
    jl(pd / "spaces" / "exterior" / "refs.jsonl", [
        {"id": "weir.PARENT", "kind": "marker"},
        {"id": "weir.HIST", "kind": "tree", "enable_parent": {"ref": "weir.PARENT", "flags": "0"}},
        {"id": "weir.DEAD", "kind": "tree", "enable_parent": {"ref": "weir.PARENT", "flags": S.OPPOSITE}},
        {"id": "weir.POT", "kind": "furniture"}])
    jl(pd / "people.jsonl", [{"id": "weir.P1", "name": "Paa-shei"}])
    jl(pd / "quests.jsonl", [{"id": "quest.q1/npc.q1.keeper", "ref": "npc.q1.keeper", "pos": [0, 0, 0]}])
    (pd / "place.json").write_text(json.dumps({"draft": {"plan": {"gives": [{"kind": "cooking-pot"}]}}}))
    return {"db": db, "quests": quests, "pdir": pd}


def gather(w):
    return P.gather("weir", w["db"], w["quests"])


def test_gather_takes_every_promising_sentence_and_only_those(world):
    got = {(c["where"], c["words"]): c["kind"] for c in gather(world)}
    words = {w for _, w in got}
    assert "The wardens hatch their eggs in the sap pool." in words
    assert "They are pious." not in words                       # names no thing, station, hour or state
    assert not any("rain" in w for w in words)                   # climate says nothing of the built place
    assert not any("tent on a platform" in w for w in words)     # another place's note
    assert "She cooks eels in the pot each morning." in words and "She is kind." not in words
    assert any(w.startswith("Paa-shei: cook at the pot") for w in words)
    assert any("asleep in the hut at night" in w for w in words)
    assert any("carried by npc.q1.keeper" in w for w in words)   # where the quest's key is
    assert "I should find the keeper in his hut." in words
    assert "Teel-Fen Weir lies south." in words and "I rest here." not in words   # elsewhere: only what names the place
    assert got[("place need 2", "the same Hist dead and blackened")] == "state"
    assert got[("Q1 ending e1 seen", "the tree at Teel-Fen Weir dead and the camp empty")] == "state"
    assert any(k[0] == "Q1 ending e1 world" for k, v in got.items() if v == "state")
    assert got[("Q1 thing thing.q1.dead source", "a dead Hist switched on at Teel-Fen Weir")] == "state"


def test_gather_keys_are_stable_and_change_with_the_words(world):
    a = {c["key"] for c in gather(world)}
    assert a == {c["key"] for c in gather(world)}
    assert P.key("x", "A pot.") != P.key("x", "A pot by the rack.")


def write_rows(w, rows):
    jl(w["pdir"] / "promises.jsonl", rows)


def full_rows(w, state_row=True):
    cands = gather(w)
    states = [c for c in cands if c["kind"] == "state"]
    rest = [c for c in cands if c["kind"] != "state"]
    rows = [{"id": "p01", "what": "everything else", "said": [{"key": c["key"]} for c in rest], "show": "added",
             "refs": ["weir.POT"], "person": "weir.P1", "give": "cooking-pot", "quest": ["quest.q1/npc.q1.keeper"],
             "verdict": "built", "why": "x"}]
    if state_row:
        rows.append({"id": "p02", "what": "the dead Hist", "said": [{"key": c["key"]} for c in states],
                     "show": "state", "state": "dead", "verdict": "built", "why": "the dead twin"})
    return rows


def states_file(w, key=("weir.DEAD",)):
    jl(w["pdir"] / "states.jsonl", [
        {"id": "living", "name": "Hist living", "default": True, "parents": {"weir.PARENT": True}, "key": ["weir.HIST"]},
        {"id": "dead", "name": "Hist dead (ending)", "set_by": {"quest": "quest.q1", "ending": "e1"},
         "parents": {"weir.PARENT": False}, "hide": ["weir.P1"], "key": list(key)}])


def faults(w):
    return P.faults("weir", w["pdir"], db=w["db"], quests=w["quests"])


def test_check_passes_a_full_list_with_its_states(world):
    write_rows(world, full_rows(world))
    states_file(world)
    assert faults(world) == []


def test_check_fails_no_list_and_an_unsaid_sentence(world):
    assert "no promise list" in faults(world)[0]
    rows = full_rows(world)
    rows[0]["said"] = rows[0]["said"][1:]
    write_rows(world, rows)
    states_file(world)
    bad = faults(world)
    assert len(bad) == 1 and bad[0].startswith("unsaid:")


def test_check_fails_missing_evidence_open_rows_and_stale_words(world):
    rows = full_rows(world)
    rows[0]["refs"] = ["weir.NOPE"]
    rows[0]["said"].append({"key": "0000000000", "where": "place note look", "words": "an old sentence"})
    rows.append({"id": "p03", "what": "a stall", "said": [], "verdict": "open"})
    rows.append({"id": "p04", "what": "nothing", "said": [], "show": "added", "verdict": "built"})
    rows.append({"id": "p05", "what": "a lie", "said": [], "verdict": "accepted", "why": ""})
    write_rows(world, rows)
    states_file(world)
    bad = "\n".join(faults(world))
    assert "ref weir.NOPE is not in the place files" in bad
    assert "no longer said" in bad
    assert "promise p03 (a stall): open" in bad
    assert "promise p04 (nothing): built with no evidence" in bad
    assert "accepted with no reason" in bad


def test_check_fails_a_quest_state_with_no_state(world):
    write_rows(world, full_rows(world, state_row=False)
               + [{"id": "p02", "what": "dead", "said": [{"key": c["key"]} for c in gather(world) if c["kind"] == "state"],
                   "show": "added", "refs": ["weir.DEAD"], "verdict": "built", "why": "x"}])
    bad = faults(world)
    assert bad and all(b.startswith("state:") for b in bad)
    write_rows(world, full_rows(world))
    bad = "\n".join(faults(world))
    assert "state dead is not in states.jsonl" in bad


def test_state_faults_and_key_refs(world):
    write_rows(world, full_rows(world))
    states_file(world, key=("weir.HIST",))           # the living tree as the dead state's key: hidden in it
    assert any("key ref weir.HIST is hidden in it" in b for b in faults(world))
    states_file(world, key=())
    assert any("dead has no key refs" in b for b in faults(world))


def test_state_resolves_as_the_game_shows_enable_parents(world):
    states_file(world)
    pd = world["pdir"]
    live, dead = S.resolve(pd, "living"), S.resolve(pd, "Hist dead (ending)")
    assert set(live["hidden"]) == {"weir.DEAD"} and set(live["shown"]) == {"weir.HIST"}
    assert set(dead["hidden"]) == {"weir.HIST", "weir.P1"} and set(dead["shown"]) == {"weir.DEAD"}
    assert S.resolve(pd)["state"]["id"] == "living"             # the default is the game's start
    with pytest.raises(KeyError):
        S.resolve(pd, "burnt")
    assert S.faults(pd) == []
    jl(pd / "states.jsonl", [{"id": "a", "key": ["weir.HIST"]}, {"id": "b", "key": ["weir.X"]}])
    bad = "\n".join(S.faults(pd))
    assert "0 default states" in bad and "state b: no set_by" in bad and "key names weir.X" in bad


ACT1 = ("outpost-m6-m66", "jal-veesa", "outpost-m13-m65", "outpost-m11-m63", "tribal-camp-m2-m68")


@pytest.mark.parametrize("place", ACT1)
def test_the_act_one_places_keep_their_promises(place):
    """Each Act I place's list says every gathered sentence with built evidence (helstrom's is made by its draft)."""
    pdir = ROOT / "newworld" / "places" / place
    assert (pdir / "promises.jsonl").exists(), f"{place} has no promise list"
    assert P.faults(place, pdir) == []
