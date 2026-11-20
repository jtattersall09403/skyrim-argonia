"""A stage runs beside hands: rows it does not own, and edits applied while it runs, are never overwritten with a stale
copy (tools/places/hands.py); ids of added things do not shift when another add is inserted or removed."""
import json

from tools.places import hands
from tools.places.draft import adds, io, stages


def _rows(p):
    return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]


def test_a_write_in_a_run_keeps_the_rows_the_hands_changed_meanwhile(tmp_path):
    root = tmp_path / "p"
    (root / "spaces" / "exterior").mkdir(parents=True)
    ext, quests = root / "spaces" / "exterior" / "refs.jsonl", root / "quests.jsonl"
    io.write_jsonl(ext, [{"id": "a", "pos": [0, 0, 0]}, {"id": "b", "pos": [1, 1, 1]}, {"id": "c", "pos": [2, 2, 2]}])
    io.write_jsonl(quests, [{"id": "q1", "spot": [1, 1, 1]}])
    with hands.beside_hands(root) as g:
        rows = io.read_jsonl(ext)
        rows[0]["pos"] = [9, 9, 9]                                         # the stage moves a
        # hands, while the stage runs: a quest spot added, b moved, a new row d added in the exterior
        quests.write_text(quests.read_text() + json.dumps({"id": "q2", "spot": [5, 5, 5]}) + "\n")
        ext.write_text(ext.read_text() + json.dumps({"id": "d", "pos": [4, 4, 4]}) + "\n")
        text = ext.read_text().replace('"id":"b","pos":[1,1,1]', '"id":"b","pos":[7,7,7]')
        ext.write_text(text)
        io.write_jsonl(ext, rows + [{"id": "e", "pos": [3, 3, 3]}])         # the stage writes its stale copy
        io.write_jsonl(quests, [{"id": "q1", "spot": [1, 1, 1]}])           # and a stale copy of what it does not own
        left = g.settle()
    got = {r["id"]: r["pos"] for r in _rows(ext)}
    assert got == {"a": [9, 9, 9], "b": [7, 7, 7], "c": [2, 2, 2], "d": [4, 4, 4], "e": [3, 3, 3]}
    assert [r["id"] for r in _rows(quests)] == ["q1", "q2"]
    assert left["spaces/exterior/refs.jsonl"] >= {"b", "d"} and "a" not in left["spaces/exterior/refs.jsonl"]


def test_a_failed_stage_puts_back_its_own_rows_and_leaves_the_hands(tmp_path):
    root = tmp_path / "p"
    root.mkdir()
    f = root / "paths.jsonl"
    io.write_jsonl(f, [{"id": "a", "n": 1}, {"id": "b", "n": 1}])
    snap = stages.snapshot(root)
    try:
        with hands.beside_hands(root) as g:
            io.write_jsonl(f, [{"id": "a", "n": 2}, {"id": "b", "n": 1}])
            f.write_text(f.read_text().replace('"id":"b","n":1', '"id":"b","n":5'))   # the hands, after the stage's write
            io.write_jsonl(f, [{"id": "a", "n": 3}, {"id": "b", "n": 1}])
            raise RuntimeError("stage failed")
    except RuntimeError:
        g.revert(snap)
    assert {r["id"]: r["n"] for r in _rows(f)} == {"a": 1, "b": 5}


def test_the_ownership_proof_leaves_out_the_hands_rows():
    before = {"quests.jsonl": '{"id":"q1","s":1}\n', "paths.jsonl": '{"id":"p","w":1}\n'}
    after = {"quests.jsonl": '{"id":"q1","s":1}\n{"id":"q2","s":2}\n', "paths.jsonl": '{"id":"p","w":2}\n'}
    _, bad = stages.diff(before, after, {"paths.jsonl": (None, True)})
    assert bad
    counts, bad = stages.diff(before, after, {"paths.jsonl": (None, True)}, {"quests.jsonl": None})
    assert not bad and list(counts) == ["paths.jsonl"]


def test_added_ids_do_not_shift_when_another_add_is_inserted_or_removed():
    bases = {b: {"key": b, "edid": b, "kind": "furniture", "bounds": [[-10, -10, 0], [10, 10, 1]]} for b in ("b:x", "b:y", "b:z")}
    place = {"draft": {"add": [{"base": "b:x", "pos": [0, 0]}, {"base": "b:y", "pos": [5, 5]}]}}
    first = {r["base"]: r["id"] for _, r in adds.rows("p", place["draft"], bases)}
    assert first["b:x"] == io.mint("p", "add", "0", "b:x") and first["b:y"] == io.mint("p", "add", "1", "b:y")   # ids as they were
    assert adds.pin(place) == 2
    place["draft"]["add"].insert(0, {"base": "b:z", "pos": [9, 9]})            # an add inserted before the others
    now = {r["base"]: r["id"] for _, r in adds.rows("p", place["draft"], bases)}
    assert now["b:x"] == first["b:x"] and now["b:y"] == first["b:y"] and now["b:z"] not in first.values()
    place["draft"]["add"].pop(1)                                                # the first one removed
    assert {r["base"]: r["id"] for _, r in adds.rows("p", place["draft"], bases)}["b:y"] == first["b:y"]
