"""tools/places/bundle.py (reader and writer) and ground_check.py on a synthetic bundle: no game data needed."""
import array
import json

import pytest

from tools.places import bundle as B
from tools.places import ground_check


def make_bundle(root, bundle_id="ground.t", esm_sha="a" * 64):
    d = root / bundle_id
    ext = d / "spaces" / "exterior"
    ext.mkdir(parents=True)
    B.write_json(d / "bundle.json", {"bundle_id": bundle_id, "kind": "ground", "spaces": ["exterior"],
                                     "esm": {"file": "W.esm", "sha256": esm_sha}, "stamp": {"key": "k"}})
    B.write_jsonl(d / "bases.jsonl", [{"key": "W.esm:000801", "kind": "tree", "nordic": False}])
    B.write_jsonl(d / "npcs.jsonl", [])
    B.write_jsonl(ext / "refs.jsonl.gz", [{"id": "W.esm:000900", "base": "W.esm:000801", "pos": [10, 20, 30]}])
    B.write_json(ext / "space.json", {"space_id": "exterior", "type": "exterior"})
    # one cell (0,0) sloping up to the east, 1 unit per unit x; one (1,0) flat at 7 with water at 5
    h = array.array("f", [c * B.STEP for r in range(B.V) for c in range(B.V)] + [7.0] * (B.V * B.V))
    (ext / "terrain.f32").write_bytes(h.tobytes())
    (ext / "terrain.json").write_text(json.dumps({"ltex": {}, "cells": [
        {"cell": [0, 0], "heights_index": 0, "water": None},
        {"cell": [1, 0], "heights_index": 1, "water": {"height": 5.0, "type": None}}]}))
    return d


def test_reader(tmp_path):
    b = B.Bundle(make_bundle(tmp_path))
    assert b.id == "ground.t" and b.space_ids == ["exterior"]
    assert b.bases["W.esm:000801"]["kind"] == "tree"
    ext = b.space("exterior")
    assert ext.refs[0]["pos"] == [10, 20, 30]          # .gz read transparently
    t = ext.terrain
    assert t.height_at(100.0, 50.0) == pytest.approx(100.0)
    assert t.height_at(5000.0, 10.0) == pytest.approx(7.0)
    assert t.height_at(-5.0, 10.0) is None
    n = t.normal_at(1000.0, 1000.0)
    assert n[0] == pytest.approx(-(0.5 ** 0.5)) and n[2] == pytest.approx(0.5 ** 0.5)
    assert t.water_at(5000.0, 10.0)["height"] == 5.0 and t.water_at(10.0, 10.0) is None
    with pytest.raises(KeyError):
        b.space("nowhere")


def test_publish_replaces_whole(tmp_path):
    final, tmp = tmp_path / "b", tmp_path / ".tmp.b"
    final.mkdir(); (final / "old").write_text("1")
    tmp.mkdir(); (tmp / "new").write_text("2")
    B.publish(tmp, final)
    assert (final / "new").exists() and not (final / "old").exists() and not tmp.exists()


def test_sha_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(B, "_SHA_CACHE", tmp_path / "c.json")
    f = tmp_path / "x"; f.write_bytes(b"abc")
    assert B.sha256_file(f) == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    assert B.sha256_file(f) == B.sha256_file(f)
    assert B.stamp_key({"a": "1"}, "t", {"p": 1}) != B.stamp_key({"a": "2"}, "t", {"p": 1})


@pytest.fixture
def gc(tmp_path, monkeypatch):
    monkeypatch.setattr(B, "_SHA_CACHE", tmp_path / "c.json")
    monkeypatch.setattr(ground_check, "BUNDLES", tmp_path / "bundles")
    esm = tmp_path / "W.esm"; esm.write_bytes(b"world")
    monkeypatch.setattr(ground_check, "ESM", esm)
    monkeypatch.setattr(ground_check, "PLAY_SHA", tmp_path / "play-esm.sha256")
    monkeypatch.setattr(ground_check, "REPO", tmp_path)
    return tmp_path, B.sha256_file(esm)


def test_ground_check_cases(gc):
    root, sha = gc
    assert not ground_check.check("t")["ok"]                          # no bundle
    make_bundle(root / "bundles", esm_sha=sha)
    r = ground_check.check("t")
    assert not r["ok"] and "absent" in r["reason"]                    # no play record: never a silent pass
    (root / "play-esm.sha256").write_text("garbage\n")
    assert not ground_check.check("t")["ok"]
    (root / "play-esm.sha256").write_text("b" * 64 + "\n")
    r = ground_check.check("t")
    assert not r["ok"] and r["play_sha"] == "b" * 64
    (root / "play-esm.sha256").write_text(sha.upper() + "\n")
    assert ground_check.check("t")["ok"]
    assert ground_check.main(["t"]) == 0


def test_ground_check_behind_build(gc):
    root, sha = gc
    make_bundle(root / "bundles", esm_sha="c" * 64)
    (root / "play-esm.sha256").write_text(sha)
    r = ground_check.check("t")
    assert not r["ok"] and "behind the built world file" in r["reason"]


def test_status_shape(gc):
    root, sha = gc
    assert ground_check.status()["match"] is False
    make_bundle(root / "bundles", esm_sha=sha)
    (root / "play-esm.sha256").write_text(sha)
    s = ground_check.status()
    assert s["match"] and s["ground_sha"] == sha == s["deployed_sha"] and s["place_id"] == "t"
