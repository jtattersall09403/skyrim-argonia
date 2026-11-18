"""The quest graph's gaps: message-box buttons are moves; a death handled, lootable or impossible is no gap."""
from tools.newworld import quest_graph as G
from tools.playtest.record import Record, world_place_names

TALK = {"topicHeardFrom": ["topic.t", "npc.a"]}


def _q(stages, placements=(), hooks=(), line="quest.line.x", qid="quest.x.q1"):
    return {"id": qid, "code": "Q1", "title": "Q", "line": line, "start": 10, "stages": stages,
            "placements": list(placements), "hooks": list(hooks), "topics": [], "cast": [{"id": "npc.a", "name": "A"}]}


def _gaps(q, records=None):
    return [g["text"] for g in G.build(q, records or {q["id"]: q})["gaps"]]


def _talk_stage(extra=()):
    return [{"id": 10, "successors": [{"to": 90, "when": TALK}, *extra]}, {"id": 90, "ending": "complete"}]


def test_unhandled_death_is_a_gap():
    assert any("dies here" in g for g in _gaps(_q(_talk_stage())))


def test_message_box_buttons_are_moves():
    q = _q([{"id": 10, "onEnter": [{"showChoice": {"text": "Pick", "buttons": [{"label": "Yes", "sets": 30},
                                                                               {"label": "No", "sets": 40}]}}]},
            {"id": 30, "ending": "complete"}, {"id": 40, "ending": "failed"}])
    assert _gaps(q) == []


def test_death_read_by_a_move_is_handled():
    assert _gaps(_q(_talk_stage([{"to": 90, "when": {"not": {"npcAlive": "npc.a"}}}]))) == []


def test_death_handled_by_a_later_quest_of_the_line():
    q = _q(_talk_stage())
    later = {"id": "quest.x.q2", "line": "quest.line.x", "startWhen": {"any": [{"not": {"npcAlive": "npc.a"}}]}}
    assert _gaps(q, {q["id"]: q, later["id"]: later}) == []
    other = later | {"line": "quest.line.y"}
    assert _gaps(q, {q["id"]: q, other["id"]: other}) != []


def test_loot_path_is_handled():
    pl = [{"ref": "thing.jar", "kind": "thing", "container": "thing.pack"}]
    assert _gaps(_q(_talk_stage([{"to": 90, "when": {"hasItem": ["thing.jar", 1]}}]), pl)) == []
    note = [{"ref": "thing.note", "kind": "thing", "carriedBy": "npc.a"}]
    hooks = [{"thing": "thing.note", "hook": "read", "setsFlag": "flag.read"}]
    assert _gaps(_q(_talk_stage([{"to": 90, "when": {"flag": "flag.read"}}]), note, hooks)) == []
    loose = [{"ref": "thing.jar", "kind": "thing", "anchor": {"place": "x"}}]   # not in a container or on a body
    assert _gaps(_q(_talk_stage([{"to": 90, "when": {"hasItem": ["thing.jar", 1]}}]), loose)) != []


def test_who_cannot_die_is_not_flagged():
    ghost = [{"ref": "npc.a", "kind": "person", "name": "A", "base": {"kind": "template_person", "id": "a ghost"}}]
    assert _gaps(_q(_talk_stage(), ghost)) == []
    ess = [{"ref": "npc.a", "kind": "person", "name": "A", "cannotDie": True}]
    assert _gaps(_q(_talk_stage(), ess)) == []


def test_playtest_names_places_by_the_world():
    pid = next(iter(world_place_names()))
    r = Record({"id": "quest.x.q", "stages": [], "placements": []})
    assert r.place_name(pid) == world_place_names()[pid]
    assert r.place_name("sunken-ruin-23-m112") == "Teku-Sul Spire"
