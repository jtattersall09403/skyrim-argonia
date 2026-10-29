"""quest_record.py: the YAML view round-trips through the rows, and import refuses a bad record whole."""
import copy

import pytest

from tools.argonia_world import db, quest_record as Q

QUESTS = ["quest.local.lh38", "quest.mr.mr01"]


@pytest.fixture
def w():
    world = db.open()
    yield world
    world.con.rollback()


def snapshot(w, qid):
    out = {}
    for node in Q._tables():
        kc = "id" if node["table"] == "quest" else "quest_id"
        out[node["table"]] = sorted(map(tuple, w.query(f'SELECT * FROM "{node["table"]}" WHERE "{kc}" = ?', qid)))
    out["fact"] = sorted(map(tuple, w.query("SELECT * FROM fact WHERE quest_id = ?", qid)))
    out["condition"] = sorted(map(tuple, w.query("SELECT * FROM condition")))
    out["action"] = sorted(map(tuple, w.query("SELECT * FROM action_arg")))
    return out


@pytest.mark.parametrize("qid", QUESTS)
def test_export_import_is_identity(w, qid):
    before = snapshot(w, qid)
    q = Q.export(w, qid)
    assert Q.import_record(w, Q.yaml.safe_load(Q.dump(q))) == []
    assert w.errors() == []
    assert snapshot(w, qid) == before
    assert Q.export(w, qid) == q


def test_unknown_field_refused(w):
    q = Q.export(w, QUESTS[0])
    q["stages"][0]["mood"] = "grim"
    errs = Q.import_record(w, q)
    assert errs and "stages[0].mood: not a field" in errs[0]


def test_dangling_key_refused_at_save(w):
    q = copy.deepcopy(Q.export(w, QUESTS[1]))
    q["cast"][0]["id"] = "npc.nobody"
    assert Q.import_record(w, q) == []
    with pytest.raises(db.LoadError) as e:
        w.save()
    assert "npc.nobody" in str(e.value)


def test_a_list_where_one_value_belongs_is_refused(w):
    q = copy.deepcopy(Q.export(w, QUESTS[0]))
    q["foundation"] = ["a", "b"]
    errs = Q.import_record(w, q)
    assert errs and "foundation: one value is expected" in errs[0]


def test_a_bad_value_leaves_the_quest_as_it_was(w):
    before = snapshot(w, QUESTS[0])
    q = copy.deepcopy(Q.export(w, QUESTS[0]))
    q["stages"][0]["journal"] = 1990                  # an int in a TEXT column, refused at insert
    errs = Q.import_record(w, q)
    assert errs and "journal" in errs[0]
    assert snapshot(w, QUESTS[0]) == before
