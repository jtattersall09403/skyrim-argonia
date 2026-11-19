"""First spots for a place's quest things (tools/places/quest_draft.py): each placement with no row gets a drafted
row on the walking mesh by what its words name; the owner's rows are never changed; the studio's payload then has a
spot for every thing; a promise a quest delivers is checked against its spots."""
import json

from tools.places import quest_draft, quest_spots
from tools.places.stock import verify
from tools.tests.test_places_quest_spots import _world


def _mesh(places):
    camp = places / "camp"
    (camp / "spaces" / "exterior").mkdir(parents=True, exist_ok=True)
    pts = [[x, y, 5.0] for x in range(0, 2001, 100) for y in range(0, 2001, 100)]
    (camp / "paths.jsonl").write_text(json.dumps({"id": "camp.path.01", "kind": "walkway", "points": pts}) + "\n")
    rows = [{"id": "camp.fire", "kind": "light", "pos": [1500.0, 1500.0, 5.0], "why": ""},
            {"id": "camp.jars", "kind": "clutter", "pos": [300.0, 1700.0, 5.0], "why": "jars of sap by the longhouse wall"}]
    (camp / "spaces" / "exterior" / "refs.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))


def test_draft_places_each_thing_by_its_words_and_keeps_the_owners(tmp_path):
    quests, places, sources = _world(tmp_path)
    _mesh(places)
    owner = quest_spots.read(places / "camp")[0]
    r = quest_draft.draft("camp", places, quests, out=tmp_path / "out", sources=sources)
    rows = {x["id"]: x for x in quest_spots.read(places / "camp")}
    assert rows["quest.main.mn04/thing.mn04.cage"] == owner                      # the owner's spot stands
    jeeta = rows.get("quest.main.mn04/npc.mn04.jeeta")
    assert jeeta is None                                                          # the place's own person: People tool
    late = rows["quest.main.mn04/npc.mn04.late"]
    assert late["drafted"] is True and late["space"] == "longhouse-1" and late["why"]
    sesk = rows["quest.main.mn04/npc.mn.sesk"]
    assert sesk["drafted"] and len(sesk["pos"]) == 3
    assert all(x.get("drafted") or x["id"] in (owner["id"], "quest.main.mn09/old") for x in rows.values())
    again = quest_draft.draft("camp", places, quests, out=tmp_path / "out", sources=sources)
    assert again["drafted"] == [] and {x["id"]: x for x in quest_spots.read(places / "camp")} == rows   # idempotent
    assert r["items"] == 4


def test_drafted_spot_stands_by_the_named_anchor_on_the_mesh(tmp_path):
    quests, places, sources = _world(tmp_path)
    _mesh(places)
    q = quests / "main" / "mn04.yaml"
    import yaml
    d = yaml.safe_load(q.read_text())
    d["placements"].append({"ref": "npc.mn04.guard-1", "kind": "person", "name": "Guard", "hostile": True, "enabled": True,
                            "level": 4, "anchor": {"place": "camp", "rule": "navmesh", "need": "at the fire pit"}})
    q.write_text(yaml.safe_dump(d))
    quest_draft.draft("camp", places, quests, out=tmp_path / "out")
    g = {x["id"]: x for x in quest_spots.read(places / "camp")}["quest.main.mn04/npc.mn04.guard-1"]
    assert 0 < ((g["pos"][0] - 1500) ** 2 + (g["pos"][1] - 1500) ** 2) ** 0.5 <= 250 and "fire" in g["why"]


def test_payload_gives_every_thing_a_spot_after_the_draft(tmp_path):
    quests, places, sources = _world(tmp_path)
    _mesh(places)
    quest_draft.draft("camp", places, quests, out=tmp_path / "out")
    items = quest_spots.payload("camp", places, quests, sources, url="")["items"]
    assert [i["id"] for i in items if not i.get("spot") and not i.get("place_person")] == []
    assert next(i for i in items if i["ref"] == "npc.mn04.late")["spot"]["drafted"] is True


def test_a_quest_delivered_promise_needs_its_spots(tmp_path):
    quests, places, sources = _world(tmp_path)
    _mesh(places)
    why = "delivered by the quest's own: quest.main.mn04/npc.mn04.late, quest.main.mn04/npc.mn04.nobody"
    probs = verify.quest_delivery_problems("camp", why, places, quests)
    assert len(probs) == 2 and "no spot yet" in probs[0] and "no placement" in probs[1]
    quest_draft.draft("camp", places, quests, out=tmp_path / "out")
    assert verify.quest_delivery_problems("camp", why, places, quests) == [probs[1]]


def test_studio_serves_every_thing_with_a_spot_after_the_draft(tmp_path, monkeypatch):
    import asyncio
    from aiohttp.test_utils import TestClient, TestServer
    quests, places, sources = _world(tmp_path)
    _mesh(places)
    quest_draft.draft("camp", places, quests, out=tmp_path / "out", sources=sources)
    for k, v in {"PLACES_OUT": tmp_path / "out", "PLACES_DIR": places, "NEWWORLD_QUESTS": quests,
                 "NEWWORLD_SOURCES": sources, "STUDIO_ZCACHE": tmp_path / "z"}.items():
        monkeypatch.setenv(k, str(v))
    for k in ("STUDIO_COMMIT", "STUDIO_BUCKET_SYNC", "STUDIO_AWAKE"):
        monkeypatch.setenv(k, "0")
    from tools.places.studio.server import make_app

    async def go():
        async with TestClient(TestServer(make_app())) as c:
            js = await (await c.get("/api/place/camp/quests")).json()
            live = [i for i in js["items"] if not i.get("orphan")]
            assert live and all(i.get("spot") or i.get("place_person") for i in live)
            assert any(i["spot"] and i["spot"].get("drafted") for i in live)
    asyncio.run(go())
