"""A place's stock key (tools/places/stock/plan.py key, part of its built check's plan key) reads its own rows of the
stock tables and the shared lookups whole: another place's stock never makes its built check stale."""
import json

from tools.places.stock import plan


def _write(d, t, rows):
    (d / f"{t}.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))


def test_only_a_places_own_rows_and_the_shared_tables_reach_its_key(tmp_path, monkeypatch):
    db = tmp_path / "db"
    db.mkdir()
    monkeypatch.setattr(plan, "DB_DIR", db)
    monkeypatch.setattr(plan, "STOCK_SRC", tmp_path / "stock")
    monkeypatch.setattr(plan, "PEOPLE_SRC", tmp_path / "people")
    rows = [{"person_id": "a.P1", "item_id": "x", "count": 1}, {"person_id": "b.P1", "item_id": "x", "count": 1}]
    _write(db, "person_item", rows)
    _write(db, "stock_loose", [{"place_id": "a", "id": "r1", "item_id": "x"}, {"place_id": "b", "id": "r1", "item_id": "x"}])
    _write(db, "lock_level", [{"id": "Novice", "level": 1}])
    k = plan.key("a")
    _write(db, "person_item", rows + [{"person_id": "b.P2", "item_id": "y", "count": 1}])     # another place's outfit
    _write(db, "stock_loose", [{"place_id": "a", "id": "r1", "item_id": "x"}, {"place_id": "b", "id": "r1", "item_id": "z"}])
    assert plan.key("a") == k
    _write(db, "person_item", rows + [{"person_id": "a.P1", "item_id": "y", "count": 1}])     # its own
    assert plan.key("a") != k
    _write(db, "person_item", rows)
    assert plan.key("a") == k
    _write(db, "lock_level", [{"id": "Novice", "level": 5}])                                   # a shared lookup
    assert plan.key("a") != k
