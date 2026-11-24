"""The owner's tree notes set that tree type's sink window in the flora table and are answered with old and new."""
import json

from tools.places import notes as N
from tools.places import tree_rules as T


def test_tree_notes_set_the_types_sink_window(tmp_path):
    (tmp_path / "x" / "edits").mkdir(parents=True)
    db = tmp_path / "flora_base.jsonl"
    db.write_text(json.dumps({"id": "ts-palm", "form_key": "004955:tropical skyrim.esp", "sink_m": 0.1}) + "\n"
                  + json.dumps({"id": "other", "form_key": "000001:x.esp", "sink_m": 0.2}) + "\n")
    placed = tmp_path / "placed"
    placed.mkdir()
    (placed / "cy-001.jsonl").write_text('{"key":"004955:Tropical Skyrim.esp"}\n{"key":"004955:Tropical Skyrim.esp"}\n{"key":"x"}\n')
    for s in (0.32, 0.4):
        N.add("x", {"text": "too high", "things": [{"id": "w", "base": "Tropical Skyrim.esp:004955", "kind": "tree", "pos": [0, 0, 0],
                                                 "world": {"base": "Tropical Skyrim.esp:004955", "pos": [0, 0, 0]}, "sink_m": s}]}, tmp_path)
    N.send("x", tmp_path)
    ch = T.plan(tmp_path, db, placed)
    assert ch[0]["new"] == {"sink_lo_m": 0.32, "sink_hi_m": 0.4, "sink_m": 0.36} and ch[0]["reseats"] == 2
    T.apply(ch, tmp_path, db)
    rows = [json.loads(ln) for ln in db.read_text().splitlines()]
    assert rows[0]["sink_lo_m"] == 0.32 and rows[1] == {"id": "other", "form_key": "000001:x.esp", "sink_m": 0.2}
    replies = [n["reply"] for n in N.read("x", tmp_path)]
    assert all("was 0.1 m and is now 0.32 to 0.4 m" in r and "all 2 of them" in r for r in replies)
