"""The small test world (tools/newworld/small): the cut, the stages it derives from the rebuild's own, the tool
runner's re-rooting, the play machine's names, and what a full run asks of it."""
import json
import struct
import sys
import types
from pathlib import Path

import numpy as np
import pytest

from tools.newworld import rebuild as R
from tools.newworld import small

BUILD = {"id": "B1", "water_level_units": 0.0, "sample_units": 128.0, "width": 32 * 40 + 1, "height": 32 * 30 + 1,
         "origin_world_x": -10 * 4096.0, "origin_world_y": 5 * 4096.0}


def test_crop_keeps_one_frame():
    """The block's origin is its north-west corner in world units; its samples are the build's own rows and columns."""
    b, rows, cols = small.crop(BUILD, (2, -6, 4, 3))
    assert (b["origin_world_x"], b["origin_world_y"]) == (2 * 4096.0, -3 * 4096.0)
    assert (b["width"], b["height"]) == (129, 97) and b["id"] == "B1-small" and b["cut_from"] == "B1"
    assert (cols.start, rows.start) == (12 * 32, 8 * 32)
    with pytest.raises(ValueError):
        small.crop(BUILD, (28, -6, 4, 3))        # past the east edge


def _real(tmp_path: Path) -> Path:
    src = tmp_path / "real"
    for d in ("terrain", "research", "plugin"):
        (src / d).mkdir(parents=True)
    h = np.arange(BUILD["width"] * BUILD["height"], dtype=np.float32).reshape(BUILD["height"], BUILD["width"])
    np.save(src / "terrain/heightmap.npy", h)
    (src / "terrain/build.json").write_text(json.dumps(BUILD))
    (src / "scope_cells.json").write_text(json.dumps([[1, -3], [2, -3], [9, 9]]))       # map cells: two world cells a side
    (src / "margin_cells.json").write_text(json.dumps([[9, 9]]))
    (src / "water_flow_cells.json").write_text(json.dumps([{"cell": [3, -5]}, {"cell": [30, 0]}]))
    for name in ("cell_region.json", "water_classified.json", "water_classified.png", "terrain/places_terrain.json",
                 "research/flora_catalogue.json", "research/hollow_extra.json", "plugin/atmosphere.json"):
        (src / name).write_text("{}")
    return src


def test_cut_crops_to_the_block_and_never_into_the_build_it_reads(tmp_path):
    src, dst = _real(tmp_path), tmp_path / "small"
    rec = small.cut(src, dst, (2, -6, 4, 4))
    h = np.load(dst / "terrain/heightmap.npy")
    whole = np.load(src / "terrain/heightmap.npy")
    assert h.shape == (129, 129) and h[0, 0] == whole[7 * 32, 12 * 32]
    b = json.loads((dst / "terrain/build.json").read_text())
    assert b["sha256"] == rec["sha256"] and len(b["sha256"]) == 64
    assert json.loads((dst / "scope_cells.json").read_text()) == [[1, -3], [2, -3]]
    assert json.loads((dst / "margin_cells.json").read_text()) == []
    assert json.loads((dst / "water_flow_cells.json").read_text()) == [{"cell": [3, -5]}]
    places = [json.loads(ln) for ln in (dst / "db/place.jsonl").read_text().splitlines()]
    assert all(small.in_block(int(p["world_x"] // 4096), int(p["world_y"] // 4096), (2, -6, 4, 4)) for p in places)
    assert (dst / "db/region.jsonl").read_bytes() == (small.REAL_DB / "region.jsonl").read_bytes()
    with pytest.raises(ValueError):
        small.cut(src, src)


def test_the_stages_are_the_rebuilds_own_under_the_small_world():
    st = {s.name: s for s in small.stages(Path("/real/out/newworld"))}
    assert list(st) == ["cut", *small.STAGES]
    for s in st.values():
        specs = [*s.reads, *s.check_reads, *s.writes, *(x for a in s.agree for x in a[:2])]
        assert not [x for x in specs if x.startswith("out:newworld/")], s.name
        assert not [a for c in (*s.cmds, *s.checks) for a in c if isinstance(a, str) and "out/newworld/" in a], s.name
        assert not s.proof and set(s.after) <= set(st)
    real = R.Tree().by_name
    for name in ("land", "landcover", "cells", "place", "paint", "mist", "navmesh"):
        # the same tool and arguments, run through the re-rooting runner; the same code read
        theirs_all = tuple(c for c in real[name].cmds if c != R.NAVMESH_SAMPLE) + real[name].checks   # the block is the fast test
        for mine, theirs in zip(st[name].cmds + st[name].checks, theirs_all):
            assert mine[:4] == (R.PY, "-m", "tools.newworld.small", "tool") and mine[4] == theirs[2]
        assert small.code_specs(st[name]) == small.code_specs(real[name])
    assert R.order(tuple(st.values()))[0] == "cut"


def test_reroot_points_a_tools_paths_and_province_wide_names_at_the_block(tmp_path, monkeypatch):
    real, db = tmp_path / "out/newworld", tmp_path / "db"
    mod = types.ModuleType("tools.fake_stage_tool")
    mod.OUT, mod.LC, mod.DB, mod.ELSE = real, real / "landcover", db / "place.jsonl", tmp_path / "other"
    mod.START_PLACE, mod.WALK = "stormhold", [1]
    tele = types.ModuleType("tools.newworld.teleports")
    tele.WALK = [{"name": "ANWWalkSwamp"}]
    monkeypatch.setitem(sys.modules, mod.__name__, mod)
    monkeypatch.setitem(sys.modules, tele.__name__, tele)
    root = tmp_path / "small"
    assert small.reroot(root, real, db) >= 3
    assert (mod.OUT, mod.LC, mod.DB, mod.ELSE) == (root, root / "landcover", root / "db/place.jsonl", tmp_path / "other")
    assert mod.START_PLACE == small.START_PLACE and mod.WALK == [1] and tele.WALK == []


def _wrld(edid: str) -> bytes:
    sub = b"EDID" + struct.pack("<H", len(edid) + 1) + edid.encode() + b"\0"
    return b"TES4" + b"\0" * 20 + b"GRUP" + b"\0" * 20 + b"WRLD" + struct.pack("<I", len(sub)) + b"\0" * 16 + sub + b"tail"


def test_rename_world_changes_one_editor_id_in_place():
    data = _wrld(small.REAL_WORLD)
    out = small.rename_world(data)
    assert len(out) == len(data) and small.PLAY_WORLD.encode() in out and small.REAL_WORLD.encode() not in out
    assert len(small.PLAY_WORLD) == len(small.REAL_WORLD)
    with pytest.raises(ValueError):
        small.rename_world(_wrld("SomeOtherWorldName"))
    with pytest.raises(ValueError):
        small.rename_world(data + _wrld(small.REAL_WORLD)[48:])      # two of them: not ours to guess


def test_real_names_gives_the_machines_logs_back_under_the_stage_tools_names(tmp_path):
    src = tmp_path / "logs"
    src.mkdir()
    (src / f"LODGen_SSE_Export_{small.PLAY_WORLD}.txt").write_text(f"x {small.PLAY_ESM} y\nmeshes\\terrain\\{small.PLAY_WORLD.lower()}\\a.btr\n")
    assert small.real_names(src, tmp_path / "back") == 1
    text = (tmp_path / f"back/LODGen_SSE_Export_{small.REAL_WORLD}.txt").read_text()
    assert small.REAL_ESM in text and small.REAL_WORLD.lower() in text and "Small" not in text


def test_a_full_run_asks_for_a_green_small_run_of_each_stale_stage_by_its_code(tmp_path):
    (tmp_path / "tools").mkdir()
    (tmp_path / "tools/land.py").write_text("v1")
    land = R.Stage("land", "", reads=("src:tools/land.py", "out:newworld/x.json"))
    other = R.Stage("terrain", "", reads=("src:tools/land.py",))          # no twin on the block: never asked
    tree = R.Tree(repo=tmp_path, stages=(land, other), py=sys.executable)
    state = tmp_path / "out/newworld-small/rebuild"
    state.mkdir(parents=True)
    assert small.unproven(tree, [land, other]) == ["land: no green small run"]
    (state / "land.json").write_text(json.dumps({"built": "k"}))          # ran, its check red
    assert small.unproven(tree, [land]) == ["land: no green small run"]
    (state / "land.json").write_text(json.dumps({"key": "k", "inputs": {"src:tools/land.py": tree.digest("src:tools/land.py")}}))
    assert small.unproven(tree, [land, other]) == []                      # proven: not asked again, whatever the data is
    (tmp_path / "tools/land.py").write_text("v2")
    fresh = R.Tree(repo=tmp_path, stages=(land,), py=sys.executable, fresh=True)
    assert small.unproven(fresh, [land]) == ["land: changed since its green small run: tools/land.py"]


def test_the_rebuilds_preflight_carries_the_small_world_row_for_the_real_stages_only(tmp_path, monkeypatch):
    monkeypatch.setattr(small, "unproven", lambda tree, stale, state=None: ["paint: no green small run"])
    monkeypatch.setattr(R, "others_running", lambda: [])
    rows = R.preflight(R.Tree(repo=tmp_path, stages=R.STAGES, py=sys.executable), [])
    hit = [r for r in rows if "small world" in r[0]]
    assert hit and hit[0][1] is False and "rebuild.sh small" in hit[0][2]
    assert not [r for r in R.preflight(R.Tree(repo=tmp_path, stages=(), py=sys.executable), []) if "small world" in r[0]]


def test_a_red_check_stops_a_run_but_not_the_small_worlds(tmp_path):
    def stages():
        bad = (sys.executable, "-c", "import sys; print('FAIL stub'); sys.exit(1)")
        touch = (sys.executable, "-c", "import pathlib; pathlib.Path('out/b.txt').write_text('b')")
        return (R.Stage("a", "", checks=(bad,), reads=("src:in.txt",)),
                R.Stage("b", "", cmds=(touch,), reads=("src:in.txt",), writes=("out:b.txt",), after=("a",)))
    (tmp_path / "in.txt").write_text("x")
    (tmp_path / "out").mkdir()
    t = R.Tree(repo=tmp_path, stages=stages(), py=sys.executable)
    done = R.Run(t, ["a", "b"], 4.0, echo=lambda *_: None).go()
    assert (done["a"]["result"], done["b"]["result"]) == ("red", "not run")
    done = R.Run(t, ["a", "b"], 4.0, echo=lambda *_: None, past_checks=True).go()
    assert (done["a"]["result"], done["b"]["result"]) == ("red", "green")
    assert not t.stamp(t.by_name["a"]).get("key")                        # red stays unproven
