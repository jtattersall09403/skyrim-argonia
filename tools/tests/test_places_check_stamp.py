"""A built check is current by the content of what the build and the checks read (check.stamp_stale), never by file
times: touching a file, the time log, a studio save or prose leave it current; a changed ref makes it stale and names
the file; so does a changed promise list (the checks read it)."""
import json
import os

from tools.places import build as B
from tools.places import check as C
from tools.places import handover


def setup(tmp_path, monkeypatch):
    root = tmp_path / "repo"
    pdir = root / "newworld/places/fen"
    (pdir / "spaces/exterior").mkdir(parents=True)
    (pdir / "place.json").write_text('{"id": "fen"}\n')
    (pdir / "spaces/exterior/refs.jsonl").write_text('{"id":"fen.a","pos":[0,0,0]}\n')
    (pdir / "promises.jsonl").write_text('{"id":"p1"}\n')
    shard = root / "out/places/shards/fen"
    shard.mkdir(parents=True)
    (shard / "world.json").write_text(json.dumps({"cells": []}))
    monkeypatch.setattr(B, "world_stamp", lambda pid, cells: {"key": "w"})
    monkeypatch.setattr(B, "place_key", lambda pdir, wk: "K:" + json.dumps(B.built_files(pdir), sort_keys=True))
    (shard / "key.txt").write_text(B.place_key(pdir, "w"))
    (shard / "check.json").write_text(json.dumps({"stamp": C.check_stamp(pdir, shard)}))
    return root, pdir


def test_times_and_unread_files_never_make_it_stale(tmp_path, monkeypatch):
    root, pdir = setup(tmp_path, monkeypatch)
    ok, line = handover.built_check_current(root, root / "out", "fen")
    assert ok, line
    for f in (pdir / "place.json", pdir / "spaces/exterior/refs.jsonl"):
        os.utime(f, (2e9, 2e9))                                             # a checkout or a merge: times only
    (pdir / "timelog.jsonl").write_text('{"t":"cmd"}\n')                     # the time log
    (pdir / "edits").mkdir()
    (pdir / "edits/save.json").write_text("{}")                            # a studio save
    (pdir / "STATE.md").write_text("notes\n")                                # prose
    ok, line = handover.built_check_current(root, root / "out", "fen")
    assert ok, line


def test_a_changed_ref_or_promise_makes_it_stale_and_names_the_file(tmp_path, monkeypatch):
    root, pdir = setup(tmp_path, monkeypatch)
    (pdir / "spaces/exterior/refs.jsonl").write_text('{"id":"fen.a","pos":[8,0,0]}\n')
    ok, line = handover.built_check_current(root, root / "out", "fen")
    assert not ok and "spaces/exterior/refs.jsonl: changed" in line
    root, pdir = setup(tmp_path / "b", monkeypatch)
    (pdir / "promises.jsonl").write_text('{"id":"p2"}\n')
    ok, line = handover.built_check_current(root, root / "out", "fen")
    assert not ok and "promises.jsonl: changed" in line


def test_a_check_with_no_stamp_says_so(tmp_path, monkeypatch):
    root, pdir = setup(tmp_path, monkeypatch)
    (root / "out/places/shards/fen/check.json").write_text("{}")
    ok, line = handover.built_check_current(root, root / "out", "fen")
    assert not ok and "no content stamp" in line
