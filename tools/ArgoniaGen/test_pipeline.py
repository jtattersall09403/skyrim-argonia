"""L1: the round trip's canonical record order (pipeline.canon) on a synthetic plugin (no game data)."""
import importlib.util
import struct
from pathlib import Path

spec = importlib.util.spec_from_file_location("pipeline", Path(__file__).with_name("pipeline.py"))
pipeline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pipeline)


def rec(sig: bytes, fid: int, body: bytes = b"") -> bytes:
    return sig + struct.pack("<IIII", len(body), 0, fid, 0) + struct.pack("<HH", 44, 0) + body


def grup(label: bytes, gtype: int, *items: bytes) -> bytes:
    body = b"".join(items)
    return b"GRUP" + struct.pack("<I", 24 + len(body)) + label + struct.pack("<iIHH", gtype, 0, 0, 0)[:12] + body


def test_canon_sorts_records_and_keeps_children_with_their_record():
    head = rec(b"TES4", 0, b"HEDR")
    kids = grup(struct.pack("<I", 0x802), 6, rec(b"REFR", 0x803))
    shuffled = head + grup(b"QUST", 0, rec(b"QUST", 0x0900_0001), rec(b"QUST", 0x0000_0005)) \
        + grup(b"CELL", 0, rec(b"CELL", 0x804), rec(b"CELL", 0x802), kids)
    ordered = head + grup(b"QUST", 0, rec(b"QUST", 0x0000_0005), rec(b"QUST", 0x0900_0001)) \
        + grup(b"CELL", 0, rec(b"CELL", 0x802), kids, rec(b"CELL", 0x804))
    assert pipeline.canon(shuffled) == ordered
    assert pipeline.canon(ordered) == ordered


def test_make_plugin_carries_the_province_navmesh(tmp_path, monkeypatch, capsys):
    """game-8: `make plugin` rebuilt ArgoniaWorld.esm without the navmesh, so no person could walk in game."""
    seen = []

    def world(data, into, sample, nav=None, veg=True):
        seen.append(nav)
        esm = tmp_path / "w.esm"
        esm.write_bytes(b"x")
        return esm

    monkeypatch.setattr(pipeline, "OUT", tmp_path)
    monkeypatch.setattr(pipeline, "world", world)
    monkeypatch.setattr(pipeline, "_terrain_stamp", lambda: "ground-1")
    monkeypatch.setattr(pipeline, "ENV", {})
    pipeline.master_world(tmp_path, rebuild=True)
    assert seen == [None] and "no province navmesh" in capsys.readouterr().out
    nav = tmp_path / "navmesh" / "province"
    nav.mkdir(parents=True)
    (nav / "build.json").write_text("{}")
    (nav / "terrain.stamp").write_text("ground-0")
    pipeline.master_world(tmp_path, rebuild=True)
    assert seen[-1] == nav and "predates the current ground" in capsys.readouterr().out
    (nav / "terrain.stamp").write_text("ground-1")
    pipeline.master_world(tmp_path, rebuild=True)
    assert seen[-1] == nav and "WARNING" not in capsys.readouterr().out


def test_plugin_skip_decision():
    skip = pipeline.skip_plugin
    assert skip("abc", "abc\n", True)          # same inputs, both ESMs there
    assert not skip("abc", "abd", True)         # an input changed
    assert not skip("abc", None, True)          # no stamp: never built, or the last build failed
    assert not skip("abc", "abc", False)        # an ESM is missing
