"""The hand-over line: the built check is current against the place files by the consistency stage's rule, by content
(a change to a room's files after the check makes it stale and is named; the owner's `edits/` and file times never do)."""
import json
import os

from tools.newworld import consistency as C
from tools.places import build as B
from tools.places import check as CK
from tools.places import handover


def place(tmp_path, monkeypatch):
    root = tmp_path / "repo"
    d = root / "newworld/places/fen"
    (d / "spaces/hut").mkdir(parents=True)
    (d / "edits").mkdir()
    for f in ("place.json", "spaces/hut/refs.jsonl", "edits/save.json"):
        (d / f).write_text("{}\n")
    shard = root / "out/places/shards/fen"
    shard.mkdir(parents=True)
    (shard / "world.json").write_text(json.dumps({"cells": []}))
    monkeypatch.setattr(B, "world_stamp", lambda pid, cells: {"key": "w"})
    monkeypatch.setattr(B, "place_key", lambda pdir, wk: "K:" + json.dumps(B.built_files(pdir), sort_keys=True))
    (shard / "key.txt").write_text(B.place_key(d, "w"))
    (shard / "check.json").write_text(json.dumps({"stamp": CK.check_stamp(d, shard)}))
    (root / "out/newworld").mkdir(parents=True)
    return root, d


def test_current_then_stale_after_a_room_edit_but_not_after_an_owner_save(tmp_path, capsys, monkeypatch):
    root, d = place(tmp_path, monkeypatch)
    ok, line = C.built_check_current(root, root / "out", "fen")
    assert ok and line.startswith("built check current")
    (d / "edits/save.json").write_text('{"ops": [1]}\n')    # the owner's save: not the draft
    os.utime(d / "spaces/hut/refs.jsonl", (3e9, 3e9))        # a newer time, the same bytes
    assert C.built_check_current(root, root / "out", "fen")[0]
    (d / "spaces/hut/refs.jsonl").write_text('{"id": "fen.a"}\n')   # the agent's last small edit, after the check
    ok, line = C.built_check_current(root, root / "out", "fen")
    assert not ok and "NOT CURRENT" in line and "spaces/hut/refs.jsonl: changed" in line
    assert handover.main(["fen", "--places-dir", str(root / "newworld/places")]) == 1
    assert "NOT CURRENT" in capsys.readouterr().out
