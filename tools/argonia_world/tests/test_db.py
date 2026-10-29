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


def test_one_bad_row_reports_only_itself(tmp_path):
    npcs = [{"id": f"npc.{i}", "name": "x"} for i in range(3)] + [{"id": "npc.z", "name": "z", "fight": 999}]
    with pytest.raises(db.LoadError) as e:
        db.load(world(tmp_path, dict(GOOD, npc=GOOD["npc"] + npcs)))
    assert [x for x in e.value.errors if "UNIQUE" in x] == [] and any("npc.z" in x for x in e.value.errors)


def test_save_of_some_tables_keeps_the_rest_dirty(tmp_path):
    w = db.load(world(tmp_path, GOOD))
    w.insert("faction", id="faction.b", name="B")
    w.insert("npc", id="npc.n", name="N")
    w.save(["faction"])
    assert w.dirty == {"npc"}
    w.save()
    assert "npc.n" in (tmp_path / db.DB_DIR / "npc.jsonl").read_text()


def test_delete_needs_the_whole_key(tmp_path):
    w = db.load(world(tmp_path, dict(GOOD, npc_faction=[
        {"npc_id": "npc.b", "ord": i, "faction_id": "faction.a"} for i in range(3)])))
    with pytest.raises(KeyError):
        w.delete("npc_faction", "npc.b")
    assert w.delete("npc_faction", npc_id="npc.b") == 3


def test_query_refuses_writes(tmp_path):
    w = db.load(world(tmp_path, GOOD))
    for sql in ("WITH x AS (SELECT 1) DELETE FROM npc_faction", "PRAGMA foreign_keys = OFF"):
        with pytest.raises(ValueError):
            w.query(sql)
    assert w.values("SELECT count(*) FROM npc_faction") == [1]
    assert w.values("PRAGMA foreign_keys") == [1] and w.query("PRAGMA table_info(npc)")[0]["name"] == "id"


@pytest.mark.parametrize("v", ["NaN", "Infinity"])
def test_non_finite_number_refused(tmp_path, v):
    p = world(tmp_path, GOOD)
    (p / db.DB_DIR / "npc.jsonl").write_text('{"id":"npc.b","name":"B","weight":%s}\n' % v)
    with pytest.raises(db.LoadError) as e:
        db.load(p)
    assert "weight" in str(e.value)


def test_cache_is_not_fresh_after_a_save_during_the_load(tmp_path):
    root = world(tmp_path, GOOD)
    a = db.load(root)                                 # process A reads the tables
    b = db.load(root)
    b.insert("faction", id="faction.new", name="N")
    b.save()                                          # process B saves one while A is still building
    db.build(a, root / db.OUT)                        # A's cache is newer than B's file, but built without it
    assert db.open(root).get("faction", "faction.new") is not None


def test_save_refuses_to_overwrite_another_writer(tmp_path):
    root = world(tmp_path, GOOD)
    a, b = db.load(root), db.load(root)
    a.insert("faction", id="faction.x", name="X")
    a.save()
    b.insert("faction", id="faction.y", name="Y")
    with pytest.raises(db.LoadError) as e:
        b.save()
    assert "changed on disk" in str(e.value)
    assert "faction.x" in (root / db.DB_DIR / "faction.jsonl").read_text()
