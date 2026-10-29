"""db.py: the load enforces types, keys and foreign keys; the write path writes sorted JSONL; a dangling key is refused."""
import json

import pytest

from tools.argonia_world import db

SCHEMA = """
CREATE TABLE faction (id TEXT PRIMARY KEY, name TEXT NOT NULL);
CREATE TABLE npc (id TEXT PRIMARY KEY, name TEXT NOT NULL, fight INTEGER CHECK (fight BETWEEN 0 AND 100),
  essential BOOLEAN, weight REAL);
CREATE TABLE npc_faction (npc_id TEXT NOT NULL REFERENCES npc(id) ON DELETE CASCADE, ord INTEGER NOT NULL,
  faction_id TEXT NOT NULL REFERENCES faction(id), PRIMARY KEY (npc_id, ord));
"""


def world(tmp_path, tables):
    (tmp_path / db.DB_DIR).mkdir(parents=True)
    (tmp_path / db.SCHEMA).write_text(SCHEMA)
    for name, rows in tables.items():
        (tmp_path / db.DB_DIR / f"{name}.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    return tmp_path


GOOD = {"faction": [{"id": "faction.a", "name": "A"}],
        "npc": [{"id": "npc.b", "name": "B", "fight": 30, "essential": True, "weight": 1}],
        "npc_faction": [{"npc_id": "npc.b", "ord": 0, "faction_id": "faction.a"}]}


def test_load_and_typed_rows(tmp_path):
    w = db.load(world(tmp_path, GOOD))
    r = w.get("npc", "npc.b")
    assert (r.name, r.fight, r.essential, r.weight) == ("B", 30, True, 1.0)
    assert [x.faction_id for x in w.rows("npc_faction", npc_id="npc.b")] == ["faction.a"]


def test_dangling_key_is_refused(tmp_path):
    bad = dict(GOOD, npc_faction=[{"npc_id": "npc.b", "ord": 0, "faction_id": "faction.nobody"}])
    with pytest.raises(db.LoadError) as e:
        db.load(world(tmp_path, bad))
    assert "faction.nobody" in str(e.value) and "has no row in faction" in str(e.value)


def test_write_path_refuses_dangling_and_writes_sorted(tmp_path):
    w = db.load(world(tmp_path, GOOD))
    w.insert("npc", id="npc.a", name="A")
    w.insert("npc_faction", npc_id="npc.a", ord=0, faction_id="faction.missing")
    with pytest.raises(db.LoadError):
        w.save()
    w.delete("npc_faction", "npc.a", 0)
    w.save()
    lines = (tmp_path / db.DB_DIR / "npc.jsonl").read_text().splitlines()
    assert [json.loads(x)["id"] for x in lines] == ["npc.a", "npc.b"]
    assert json.loads(lines[1]) == {"id": "npc.b", "name": "B", "fight": 30, "essential": True, "weight": 1.0}


def test_types_and_checks(tmp_path):
    for bad in ({"id": "npc.c", "name": "C", "fight": "high"}, {"id": "npc.c", "name": "C", "fight": 101},
                {"id": "npc.c", "fight": 1}, {"id": "npc.c", "name": "C", "nope": 1}):
        with pytest.raises(db.LoadError):
            db.load(world(tmp_path / str(len(str(bad))) / bad["id"], dict(GOOD, npc=GOOD["npc"] + [bad])))
