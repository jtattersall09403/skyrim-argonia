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


def _key(world, thing, line="many-root", name="many-root.md"):
    return N.row_key(world["lines"] / name, line, thing)


def _judged(world):
    hall = _key(world, "a hall that can be entered")
    doc = {"place_id": "fenwick", "dismissed": [], "needs": [
        {"seq": 0, "from": [hall], "thing": "a hall that can be entered", "line": "many-root",
         "signs": [{"sign": "label", "detail": "its door shows \"Hall\""},
                   {"sign": "person", "detail": "the healer names it", "person": "fenwick.B"}],
         "rests": {"space": "hall"}, "met": True, "why": "Met. Its door shows Hall."},
        {"seq": 1, "from": ["gone000000"], "thing": "a crocodile", "line": "main", "signs": [], "rests": None,
         "placed": [{"person": "fenwick.A"}], "met": False, "why": "Not met. No creatures.", "fit": "the wild ground"}]}
    N.write(doc, world["root"])
    (world["places"] / "fenwick" / "spaces" / "exterior" / "refs.jsonl").write_text(
        json.dumps({"id": "fenwick.door", "pos": [0, 0, 0]}) + "\n"
        + json.dumps({"id": "fenwick.urn", "pos": [1, 1, 0], "name": "Sealed Urn", "need": 1}) + "\n")


def _compose(world):
    return N.compose("fenwick", world["root"], world["people"], world["lines"], {"fenwick"}, world["places"],
                     world["tmp"] / "roster.md")


def test_the_panel_is_made_from_the_stories(world):
    _judged(world)
    d = _compose(world)
    hall = d["needs"][0]
    assert hall["seq"] == 0 and hall["met"] and hall["judged"] and hall["line"] == "a faction of healers (Many-Root)"
    assert hall["does"] == "briefings" and hall["sources"][0]["story"] == "lines/many-root.md:11"
    assert hall["know"] == 'By the name the game shows: its door shows "Hall". Told by a person: the healer names it.'
    open_ = [n for n in d["needs"] if not n["judged"]]
    assert {n["thing"] for n in open_} == {"a spot by the hall's door", "a crocodile on the mud", "a keeper's post",
                                           "a gate that locks"}
    assert all(n["seq"] is None and not n["met"] for n in open_)
    gone = d["changed_story"]
    assert gone[0]["was_for"] == "a crocodile"
    assert [(t["kind"], t["name"]) for t in gone[0]["placed"]] == [("thing", "Sealed Urn"), ("person", "Xilsa")]
    assert d["people"]["fenwick.A"]["uses"] == [] and d["people"]["fenwick.B"]["uses"] == []


def test_a_story_marked_to_be_rewritten_marks_its_rows_and_a_replaced_one_is_not_read(world):
    _judged(world)
    p = world["lines"] / "many-root.md"
    p.write_text(STORY.replace("# A line\n", "# A line\n\n**Status: to be rewritten.** Section 4 is untrue.\n"
                               "\nXilsa tends the roots by the hall.\n"))
    d = _compose(world)
    assert d["needs"][0]["rewrite"] and d["needs"][0]["judged"]                 # a status line moves no key
    uses = d["people"]["fenwick.A"]["uses"]
    assert uses[0]["for"] == "Xilsa tends the roots by the hall." and uses[0]["rewrite"]
    p.write_text(STORY.replace("# A line\n", "# A line\n\n**Status: replaced by the plot.**\n"))
    d = _compose(world)
    assert [n["thing"] for n in d["needs"]] == ["a keeper's post", "a gate that locks", "a gate that locks"]
    assert d["changed_story"][0]["seq"] == 0 and d["changed_story"][1]["seq"] == 1
    (world["lines"] / "many-root-newworld.md").write_text("# Twin\n")
    assert [p.stem for p, _ in N.stories(world["lines"])] == ["many-root-newworld", "province-plan"]


def test_who_words_and_check_hold_rests_to_the_place_files(world):
    _judged(world)
    who = N.who_words("fenwick", world["people"])
    assert who["fenwick.A"]["who"] == "Xilsa, an Argonian woman: root-tender; grown child in Taleeka's household."
    assert N.check("fenwick", world["root"], world["places"], world["people"]) == []
    doc = N.read("fenwick", world["root"])
    doc["needs"][0]["rests"] = {"space": "exterior", "ref": "fenwick.gone"}
    doc["needs"][1].pop("fit")
    doc["needs"][1]["placed"] = [{"person": "fenwick.Z"}]
    N.write(doc, world["root"])
    errs = N.check("fenwick", world["root"], world["places"], world["people"])
    assert any("no ref fenwick.gone" in e for e in errs) and any("no fit" in e for e in errs)
    assert any("no person fenwick.Z" in e for e in errs)


def test_owner_changes_are_recorded_and_listed(world):
    _judged(world)
    with pytest.raises(ValueError):
        N.record_change("fenwick", {"need": 0, "change": "burnt", "what": "x"}, world["root"])
    with pytest.raises(ValueError):
        N.record_change("fenwick", {"need": 9, "change": "removed", "what": "x"}, world["root"])
    row = N.record_change("fenwick", {"need": 0, "change": "removed", "what": "the hall's door: removed",
                                      "save": "autosave"}, world["root"])
    assert row["tier"] == "OWNER_STATED"
    N.record_change("fenwick", {"person": "fenwick.A", "change": "renamed", "what": "renamed from Xilsa to Xil"},
                    world["root"])
    text = N.changed_listing(["fenwick"], world["root"])
    assert "removed by the owner (OWNER_STATED) - need 0: a hall that can be entered" in text
    assert "renamed from Xilsa to Xil" in text and "in save autosave" in text
    assert _compose(world)["needs"][0]["changed"][0]["change"] == "removed"


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
    assert after["place_need"], "Helstrom's judgements are in the database"


def test_helstrom_shows_the_plot_and_not_the_old_spring():
    d = N.payload("helstrom")
    things = " ".join(n["thing"] for n in d["needs"])
    assert "the Reed's handler" in things and "go-between" in things
    assert "boatman" not in things and "crocodile" not in things
    gone = " ".join(t.get("name") or "" for c in d["changed_story"] for t in c["placed"])
    assert "Sealed Spring" in gone and "Ruxa-Neel" in gone and "Wujeel" in gone


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
            assert d["place_id"] == "fenwick" and "a crocodile" in [c["was_for"] for c in d["changed_story"]]
            r = await c.post("/api/place/fenwick/needs/changed", json={"need": 0, "change": "moved", "what": "moved 40 m"})
            assert r.status == 200 and (await r.json())["tier"] == "OWNER_STATED"
            assert (await c.post("/api/place/fenwick/needs/changed", json={"change": "moved", "what": "x"})).status == 400
            assert (await c.post("/api/place/fenwick/needs/changed", data=b"nope")).status == 400
            assert N.changes("fenwick", world["root"])[0]["what"] == "moved 40 m"
    asyncio.run(go())
