"""The quest record's information plan and terms (quest-write/quest-record.md §1, §2 11b): import and export carry a
stage's `information` {going, next, ways, carriers} and a quest's `terms` unchanged."""
from tools.argonia_world import db
from tools.argonia_world.quest_record import export, import_record, to_rows

INFO = {"going": "Nesh-Deeka wants the jar Dives-Without-A-Rope carried off.",
        "next": "Ask Dives-Without-A-Rope for the jar, in the ship's hold.",
        "ways": ["ask her for it", "pick her lockbox"],
        "carriers": [{"know": "the jar is Dives's", "by": ["journal", "line:topic.bc01-owing"]},
                     {"know": "where she is", "by": ["objective", "marker:npc.nesh-deeka"]}]}
TERMS = [{"term": "Nine Bends", "meets": "10 line:topic.bc01-owing", "told": "Dives's own Hist tree",
          "ask": "topic.bc01-owing"},
         {"term": "the Owing", "meets": "10 journal"}]


def test_information_and_terms_round_trip():
    w = db.load()
    q = export(w, "quest.bc.bc01")
    q["stages"][0]["information"] = INFO
    q["terms"] = TERMS
    assert import_record(w, q) == [] and w.errors() == []
    back = export(w, "quest.bc.bc01")
    assert back["stages"][0]["information"] == INFO
    assert back["terms"] == TERMS
    assert back == q


def test_an_unknown_information_field_is_refused():
    q = export(db.load(), "quest.bc.bc01")
    q["stages"][0]["information"] = {**INFO, "mood": "tense"}
    assert any("information.mood" in e for e in to_rows(q).errors)
