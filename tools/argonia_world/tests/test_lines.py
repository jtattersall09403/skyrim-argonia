"""lines.py: written dialogue lines round-trip through dialogue_line rows; a bad file is refused whole; the
imported reference lines are never touched."""
import copy

import pytest

from tools.argonia_world import db, lines as L

LIVIA = "npc.imperial-fringe.claywater-station.well-keeper"
DOC = {
    "speaker": LIVIA,
    "place": "place.imperial-fringe.claywater-station",
    "lines": [
        {"id": "line.test.livia.greeting", "type": "greeting", "low": "Low.", "words": "Mid.", "high": "High.",
         "facts": ["fact.claywater-station.why-founding-2"], "links": ["topic.claywater-station"]},
        {"id": "line.test.livia.two-charges", "type": "dialogue", "topic": "topic.claywater-two-charges",
         "available": {"questStage": ["quest.local.lf83", ">=", 10]}, "words": "Two drakes a skin.",
         "onDelivered": [{"setFlag": ["flag.lf83.test", True]}]},
    ],
}


@pytest.fixture
def w():
    world = db.open()
    yield world
    world.con.rollback()


def imported_reference(w):
    return sorted(map(tuple, w.query("SELECT * FROM dialogue_line WHERE speaker = ? AND id NOT LIKE 'line.%'", LIVIA)))


def test_round_trip(w):
    before = imported_reference(w)
    assert L.import_lines(w, copy.deepcopy(DOC)) == []
    assert w.errors() == []
    got = L.export(w, LIVIA)
    mine = [ln for ln in got["lines"] if ln["id"].startswith("line.test.")]
    assert mine == [{k: v for k, v in ln.items()} for ln in DOC["lines"]]
    assert imported_reference(w) == before


def test_reimport_replaces(w):
    assert L.import_lines(w, copy.deepcopy(DOC)) == []
    doc = copy.deepcopy(DOC)
    doc["lines"] = doc["lines"][:1]
    assert L.import_lines(w, doc) == []
    ids = w.values("SELECT id FROM dialogue_line WHERE id LIKE 'line.test.%'")
    assert ids == ["line.test.livia.greeting"]
    assert w.values("SELECT id FROM condition WHERE id = 'dialogue_line:line.test.livia.two-charges:available'") == []


@pytest.mark.parametrize("mutate, needle", [
    (lambda d: d["lines"][1].update(available={"rumourHeard": ["x"]}), "not a condition term"),
    (lambda d: d["lines"][1].update(onDelivered=[{"teleport": ["x"]}]), "not one action"),
    (lambda d: d["lines"][0].update(id="greeting.test"), "starts 'line.'"),
    (lambda d: d["lines"][0].update(facts=["fact.no-such"]), "dangling"),
    (lambda d: d["lines"][1].pop("topic"), "answers a topic"),
    (lambda d: d["lines"][0].update(colour="red"), "unknown key"),
])
def test_bad_file_refused_whole(w, mutate, needle):
    doc = copy.deepcopy(DOC)
    mutate(doc)
    errs = L.import_lines(w, doc)
    assert any(needle in e for e in errs), errs
    assert w.values("SELECT id FROM dialogue_line WHERE id LIKE 'line.test.%'") == []
