"""The things the quests put at a place (tools/places/quest_spots.py): what the studio shows of each, its links into
the story explorer, its one spot in the place's quests.jsonl, and the studio's endpoint and offline list."""
import asyncio
import json
from pathlib import Path

import yaml
from aiohttp.test_utils import TestClient, TestServer

from tools.places import edits, quest_spots

URL = "https://claude.ai/artifact/X"


def _world(t: Path):
    quests, places, sources = t / "quests", t / "places", t / "sources"
    (quests / "main").mkdir(parents=True)
    camp = {"id": "quest.main.mn04", "code": "MN04", "title": "The Sap Camp", "start": 10,
            "stages": [{"id": 10, "journalText": "Free Sesk."}, {"id": 20, "journalText": "Sesk is free."}],
            "placements": [
                {"ref": "npc.mn.sesk", "kind": "person", "name": "Sesk", "enabled": True,
                 "anchor": {"place": "camp", "rule": "navmesh", "need": "inside the cage", "room": "Sesk's Cage"}},
                {"ref": "thing.mn04.cage", "kind": "door", "name": "Sesk's Cage", "enabled": True,
                 "lock": {"level": "novice"}, "anchor": {"place": "camp", "rule": "surface", "need": "at the west edge"}},
                {"ref": "npc.mn04.jeeta", "kind": "person", "name": "Jeeta", "enabled": True, "hostile": True,
                 "anchor": {"place": "camp", "rule": "navmesh", "need": "at the fire"}},
                {"ref": "npc.mn04.late", "kind": "person", "name": "Late", "enabled": False,
                 "anchor": {"place": "camp", "rule": "navmesh", "need": "in the longhouse", "room": "Longhouse"}},
                {"ref": "npc.mn04.far", "kind": "person", "name": "Far", "enabled": True,
                 "anchor": {"place": "elsewhere", "rule": "navmesh", "need": "x"}}],
            "endings": [{"id": "e-sent", "when": "Sesk was sent home", "world": [{"disableRef": "npc.mn.sesk"}]}]}
    later = {"id": "quest.main.mn05", "code": "MN05", "title": "After", "start": 10,
             "stages": [{"id": 10}, {"id": 30, "journalText": "Someone came.", "onEnter": [{"enableRef": "npc.mn04.late"}]}]}
    (quests / "main" / "mn04.yaml").write_text(yaml.safe_dump(camp))
    (quests / "main" / "mn05.yaml").write_text(yaml.safe_dump(later))
    (places / "camp" / "spaces" / "longhouse-1").mkdir(parents=True)
    (places / "camp" / "place.json").write_text(json.dumps({"place_id": "camp"}))
    (places / "camp" / "spaces" / "longhouse-1" / "space.json").write_text(json.dumps({"space_id": "longhouse-1", "name": "Longhouse"}))
    spot = {"id": "quest.main.mn04/thing.mn04.cage", "quest": "quest.main.mn04", "ref": "thing.mn04.cage",
            "space": "exterior", "pos": [10, 20, 3], "rot": [0, 0, 1.57]}
    gone = {"id": "quest.main.mn09/old", "quest": "quest.main.mn09", "ref": "old", "space": "exterior", "pos": [0, 0, 0], "rot": [0, 0, 0]}
    (places / "camp" / "quests.jsonl").write_text(json.dumps(spot) + "\n" + json.dumps(gone) + "\n")
    (sources / "people").mkdir(parents=True)
    (sources / "people" / "camp.json").write_text(json.dumps({"people": [{"id": "camp.p1", "name": "Jeeta", "cast": "npc.mn04.jeeta"}]}))
    return quests, places, sources


def test_payload_says_when_each_thing_is_in_the_world_and_links_its_stage(tmp_path):
    quests, places, sources = _world(tmp_path)
    d = quest_spots.payload("camp", places, quests, sources, url=URL)
    by = {i["ref"]: i for i in d["items"]}
    assert set(by) == {"npc.mn.sesk", "thing.mn04.cage", "npc.mn04.jeeta", "npc.mn04.late", "old"}   # not another place's
    sesk = by["npc.mn.sesk"]
    assert sesk["appears"]["url"] == f"{URL}#q-mn04/s-10" and "from the start of the game" in sesk["appears"]["words"]
    assert sesk["gone"][0]["words"].startswith("Goes at an ending of MN04 The Sap Camp: Sesk was sent home")
    assert sesk["quest_url"] == f"{URL}#q-mn04" and sesk["spot"] is None and sesk["space"] == "exterior"   # no such room
    late = by["npc.mn04.late"]
    assert late["appears"]["url"] == f"{URL}#q-mn05/s-30" and "MN05 After reaches stage 30" in late["appears"]["words"]
    assert late["space"] == "longhouse-1"
    assert by["thing.mn04.cage"]["spot"]["pos"] == [10, 20, 3] and by["thing.mn04.cage"]["lock"] == {"level": "novice"}
    assert by["npc.mn04.jeeta"]["place_person"] == {"id": "camp.p1", "name": "Jeeta"}
    assert by["old"]["orphan"]
    assert quest_spots.check("camp", places, quests) == ["quest.main.mn09/old: a spot no quest record asks for"]


def test_a_move_is_written_to_the_one_spot_file(tmp_path):
    quests, places, sources = _world(tmp_path)
    files = edits.load_place(places / "camp", sources)
    row = files["quests"][0]
    moved = dict(row, pos=[50, 60, 4])
    sesk = {"id": "quest.main.mn04/npc.mn.sesk", "quest": "quest.main.mn04", "ref": "npc.mn.sesk", "space": "exterior",
            "pos": [1, 2, 3], "rot": [0, 0, 0]}
    out = edits.apply(files, [{"n": 1, "op": "quest.edit", "quest": moved, "before": row},
                              {"n": 2, "op": "quest.add", "quest": sesk}])
    edits.write_place(places / "camp", out, sources)
    d = quest_spots.payload("camp", places, quests, sources, url=URL)
    spots = {i["ref"]: i["spot"] for i in d["items"]}
    assert spots["thing.mn04.cage"]["pos"] == [50, 60, 4] and spots["npc.mn.sesk"]["pos"] == [1, 2, 3]


def test_studio_serves_quests_and_lists_them_offline(tmp_path, monkeypatch):
    quests, places, sources = _world(tmp_path)
    for k, v in {"PLACES_OUT": tmp_path / "out", "PLACES_DIR": places, "NEWWORLD_QUESTS": quests,
                 "NEWWORLD_SOURCES": sources, "STUDIO_ZCACHE": tmp_path / "z"}.items():
        monkeypatch.setenv(k, str(v))
    for k in ("STUDIO_COMMIT", "STUDIO_BUCKET_SYNC", "STUDIO_AWAKE"):
        monkeypatch.setenv(k, "0")
    from tools.places.studio.server import make_app

    async def go():
        async with TestClient(TestServer(make_app())) as c:
            r = await c.get("/api/place/camp/quests")
            assert r.status == 200
            js = await r.json()
            assert {i["ref"] for i in js["items"]} >= {"npc.mn.sesk", "thing.mn04.cage"} and len(js["spots"]) == 2
            assert (await c.get("/api/place/Bad!/quests")).status in (400, 404)
    asyncio.run(go())
    src = (Path(quest_spots.__file__).parent / "studio" / "offline.py").read_text()
    assert '"quests"' in src
