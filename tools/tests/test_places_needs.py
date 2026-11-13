"""What the stories need of a place (tools/places/needs.py, tools/newworld/needsdb.py): reading the line stories'
needs tables, proposing, confirming and dismissing, the owner's changes, the plain words, the check, the database
tables and the studio's two endpoints."""
import asyncio
import json
from pathlib import Path

import pytest
from aiohttp.test_utils import TestClient, TestServer

from tools.places import needs as N

STORY = """# A line

## 4. What each quest needs of its places

Intro.

**Fenwick** (D somewhere; drafted).

| The thing | Quest | What happens there | How the player knows it |
|---|---|---|---|
| a hall that can be entered | all | briefings | its door is named "Hall" |
| a spot by the hall's door | MR01 | their lines | |

**Elsewhere** (D x).

| The thing | Quest | What happens there |
|---|---|---|
| a pier | MR02 | a boat |

**Later acts.**

| Place | The thing | Quest |
|---|---|---|
| Fenwick | a crocodile on the mud | MQ04 |
| Gideon | a stall | MQ05 |

| Place | The note as it stands | What it should say |
|---|---|---|
| Fenwick | a note | not a need |

## 5. Read on paper

| The thing | Quest |
|---|---|
| outside the section | X |
"""
PLAN = """## Needs of places

| Place | The thing needed | Line |
|---|---|---|
| Fenwick | a keeper's post | Waykeepers |
| Fenwick | a gate that locks | Chainbreakers, Main |
"""


@pytest.fixture
def world(tmp_path):
    lines = tmp_path / "lines"
    lines.mkdir()
    (lines / "many-root.md").write_text(STORY)
    (lines / "province-plan.md").write_text(PLAN)
    root = tmp_path / "needs"
    root.mkdir()
    (root / "lines.json").write_text(json.dumps({"lines": [
        {"id": "many-root", "name": "Many-Root", "plain": "a faction of healers"},
        {"id": "main", "name": "the main quest", "plain": "the main story"}]}))
    people = tmp_path / "people"
    people.mkdir()
    (people / "fenwick.json").write_text(json.dumps({"place_id": "fenwick", "households": [], "people": [
        {"id": "fenwick.A", "name": "Xilsa", "sex": "female", "race": "ArgonianRace", "trade": "root-tender",
         "household": {"id": "h1", "role": "grown child"}},
        {"id": "fenwick.B", "name": "Taleeka", "sex": "female", "race": "ArgonianRace", "trade": "healer",
         "household": {"id": "h1", "role": "head"}}]}))
    places = tmp_path / "places"
    (places / "fenwick" / "spaces" / "exterior").mkdir(parents=True)
    (places / "fenwick" / "spaces" / "exterior" / "refs.jsonl").write_text(json.dumps({"id": "fenwick.door", "pos": [0, 0, 0]}) + "\n")
    (places / "fenwick" / "spaces" / "hall").mkdir()
    N.ROOT = tmp_path   # story locators are written relative to the root
    yield {"root": root, "lines": lines, "people": people, "places": places, "tmp": tmp_path}
    N.ROOT = Path(N.__file__).resolve().parents[2]


def test_tables_are_read_for_the_place_only(world):
    rows = N.read_tables(world["lines"] / "many-root.md", {"fenwick"})
    assert [r["thing"] for r in rows] == ["a hall that can be entered", "a spot by the hall's door",
                                          "a crocodile on the mud"]
    assert rows[0]["know"] == 'its door is named "Hall"' and rows[0]["quests"] == "all" and rows[0]["line"] == "many-root"
    assert rows[0]["story"] == "lines/many-root.md:11"
    plan = N.read_tables(world["lines"] / "province-plan.md", {"fenwick"})
    assert [(r["line"], r["thing"]) for r in plan] == [("waykeepers", "a keeper's post"),
                                                       ("chainbreakers", "a gate that locks"), ("main", "a gate that locks")]


def test_propose_confirm_dismiss_round(world):
    props = N.propose("fenwick", world["root"], world["lines"], {"fenwick"})
    assert len(props) == 6
    hall = next(p for p in props if p["thing"].startswith("a hall"))
    need = N.confirm("fenwick", hall["key"], root=world["root"])
    assert need["seq"] == 0 and need["met"] is False and need["firmness"] == "first-draft"
    croc = next(p for p in props if "crocodile" in p["thing"])
    N.confirm("fenwick", croc["key"], into=0, root=world["root"])
    gate = next(p for p in props if p["line"] == "main")
    N.dismiss("fenwick", gate["key"], "the gate belongs to another place", root=world["root"])
    again = N.propose("fenwick", world["root"], world["lines"], {"fenwick"})
    assert len(again) == 3 and not {hall["key"], croc["key"], gate["key"]} & {p["key"] for p in again}
    assert N.read("fenwick", world["root"])["needs"][0]["stories"] == ["lines/many-root.md:11", "lines/many-root.md:24"]
    with pytest.raises(ValueError):
        N.confirm("fenwick", "nope", root=world["root"])


def _judged(world):
    doc = {"place_id": "fenwick", "proposed": [], "dismissed": [], "needs": [
        {"seq": 0, "thing": "a hall that can be entered", "line": "many-root", "quests": "every quest",
         "does": "The player takes each job inside.", "firmness": "first-draft",
         "signs": [{"sign": "label", "detail": "its door shows \"Hall\""},
                   {"sign": "person", "detail": "the healer names it", "person": "fenwick.B"}],
         "rests": {"space": "hall"}, "met": True, "why": "Met. Its door shows Hall."},
        {"seq": 1, "thing": "a crocodile", "line": "main", "quests": "the fourth main quest",
         "does": "The player kills it.", "firmness": "first-draft", "signs": [], "rests": None, "met": False,
         "why": "Not met. No creatures.", "fit": "the wild ground outside"}],
        "people": [{"person": "fenwick.A", "seq": 0, "line": "many-root", "quests": "every quest",
                    "for": "Tends the roots.", "keep": "reachable", "firmness": "first-draft", "story": "x.md:1"}]}
    N.write(doc, world["root"])


def test_payload_is_plain_and_check_holds_rests_to_the_place_files(world):
    _judged(world)
    d = N.payload("fenwick", world["root"], world["people"])
    hall, croc = d["needs"]
    assert hall["line"] == "a faction of healers (Many-Root)" and hall["met"] and hall["first_draft"]
    assert hall["know"] == 'By the name the game shows: its door shows "Hall". Told by a person: the healer names it.'
    assert croc["know"].startswith("The story does not yet say")
    assert d["people"]["fenwick.A"]["who"] == "Xilsa, an Argonian woman: root-tender; grown child in Taleeka's household."
    assert d["people"]["fenwick.A"]["uses"][0]["keep"] == "to stand where the player can speak to them"
    assert d["people"]["fenwick.B"]["uses"] == []
    assert N.check("fenwick", world["root"], world["places"], world["people"]) == []
    doc = N.read("fenwick", world["root"])
    doc["needs"][0]["rests"] = {"space": "exterior", "ref": "fenwick.gone"}
    doc["needs"][1].pop("fit")
    N.write(doc, world["root"])
    errs = N.check("fenwick", world["root"], world["places"], world["people"])
    assert any("no ref fenwick.gone" in e for e in errs) and any("no fit" in e for e in errs)


def test_owner_changes_are_recorded_and_listed(world):
    _judged(world)
    with pytest.raises(ValueError):
        N.record_change("fenwick", {"need": 0, "change": "burnt", "what": "x"}, world["root"])
    with pytest.raises(ValueError):
        N.record_change("fenwick", {"need": 9, "change": "removed", "what": "x"}, world["root"])
    with pytest.raises(ValueError):
        N.record_change("fenwick", {"person": "fenwick.B", "change": "removed", "what": "x"}, world["root"])
    row = N.record_change("fenwick", {"need": 0, "change": "removed", "what": "the hall's door: removed",
                                      "save": "autosave"}, world["root"])
    assert row["tier"] == "OWNER_STATED"
    N.record_change("fenwick", {"person": "fenwick.A", "change": "renamed", "what": "renamed from Xilsa to Xil"},
                    world["root"])
    text = N.changed_listing(["fenwick"], world["root"])
    assert "removed by the owner (OWNER_STATED) - need 0: a hall that can be entered" in text
    assert "renamed from Xilsa to Xil" in text and "in save autosave" in text
    assert N.payload("fenwick", world["root"], world["people"])["needs"][0]["changed"][0]["change"] == "removed"


def test_the_committed_database_rows_are_the_sources_loaded():
    from tools.argonia_world import db
    from tools.newworld import frame as f
    from tools.newworld import needsdb
    w = db.open(f.ROOT, cache=False)
    before = {t: sorted(tuple(r) for r in w.query(f'SELECT * FROM "{t}"')) for t in needsdb.TABLES}
    needsdb.clear(w)
    needsdb.load(w)
    after = {t: sorted(tuple(r) for r in w.query(f'SELECT * FROM "{t}"')) for t in needsdb.TABLES}
    assert before == after, "run `python -m tools.places needs load` after changing newworld/sources/needs"
    assert after["place_need"], "Helstrom's needs are in the database"


def test_studio_endpoints(world, monkeypatch, tmp_path):
    _judged(world)
    src = tmp_path / "sources"
    src.mkdir()
    (src / "needs").symlink_to(world["root"])
    (src / "people").symlink_to(world["people"])
    for k, v in {"NEWWORLD_SOURCES": src, "PLACES_OUT": tmp_path / "out", "PLACES_DIR": world["places"],
                 "STUDIO_COMMIT": "0", "STUDIO_BUCKET_SYNC": "0", "STUDIO_AWAKE": "0"}.items():
        monkeypatch.setenv(k, str(v))
    from tools.places.studio.server import make_app

    async def go():
        async with TestClient(TestServer(make_app())) as c:
            d = await (await c.get("/api/place/fenwick/needs")).json()
            assert [n["met"] for n in d["needs"]] == [True, False]
            r = await c.post("/api/place/fenwick/needs/changed", json={"need": 0, "change": "moved", "what": "moved 40 m"})
            assert r.status == 200 and (await r.json())["tier"] == "OWNER_STATED"
            assert (await c.post("/api/place/fenwick/needs/changed", json={"change": "moved", "what": "x"})).status == 400
            assert (await c.post("/api/place/fenwick/needs/changed", data=b"nope")).status == 400
            d = await (await c.get("/api/place/fenwick/needs")).json()
            assert d["needs"][0]["changed"][0]["what"] == "moved 40 m"
    asyncio.run(go())
