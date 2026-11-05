"""L1: the round trip's canonical record order (pipeline.canon) on a synthetic plugin (no game data)."""
import importlib.util
import struct

import pytest
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
    monkeypatch.setattr(pipeline, "_terrain_stamp", lambda ground=True: "ground-1")
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


def test_freeze_ground_copies_the_field_and_keeps_the_last_two(tmp_path):
    t = tmp_path / "terrain"
    t.mkdir()
    for n in pipeline.FROZEN_FILES:
        (t / n).write_bytes(b"v1")
    for i, s in enumerate(("aaa", "bbb", "ccc")):
        (t / "ground-f32.npy").write_bytes(f"v{i}".encode())
        frozen = pipeline.freeze_ground(t / "ground-f32.npy", s)
        assert frozen == t / "build" / s / "ground-f32.npy"
        for n in pipeline.FROZEN_FILES:
            assert (frozen.parent / n).exists()
        import os
        os.utime(frozen.parent, (1000 + i, 1000 + i))
    (t / "ground-f32.npy").write_bytes(b"overwritten by a lane")  # the shared file changes under a build
    assert frozen.read_bytes() == b"v2"
    assert sorted(p.name for p in (t / "build").iterdir()) == ["bbb", "ccc"]


def test_world_hands_the_frozen_ground_to_every_stage(tmp_path, monkeypatch):
    frozen = tmp_path / "terrain" / "build" / "abc" / "ground-f32.npy"
    calls = []

    def fake_run(*cmd, capped=False, quiet=True):
        calls.append([str(c) for c in cmd])
        if cmd[0] == "gen" and "--out" in cmd:  # the generator's stages write their --out
            Path(cmd[list(cmd).index("--out") + 1]).write_bytes(b"esm")
        return ""

    class Done:
        returncode = 0
        stdout = stderr = ""

    def fake_sub(cmd, **kw):
        for i, c in enumerate(cmd):  # the generator writes its --out
            if c == "--out":
                Path(cmd[i + 1]).write_bytes(b"esm")
        return Done()

    monkeypatch.setattr(pipeline, "ground", lambda: frozen)
    monkeypatch.setattr(pipeline, "run", fake_run)
    monkeypatch.setattr(pipeline.subprocess, "run", fake_sub)
    monkeypatch.setattr(pipeline, "water", lambda into, sample: into / "water")
    monkeypatch.setattr(pipeline, "_terrain_stamp", lambda ground=True: "s")
    monkeypatch.setattr(pipeline, "_veg_stamp", lambda: "v")
    for f in ("_ground_stamp", "_water_stamp", "_creature_key"):
        monkeypatch.setattr(pipeline, f, lambda: f)
    monkeypatch.setattr(pipeline, "STAGE_DIR", tmp_path / "stages")
    monkeypatch.setattr(pipeline, "_refuse_shared_rebuild", lambda into: None)
    monkeypatch.setattr(pipeline, "WORLD_CAP", [])
    monkeypatch.setattr(pipeline, "CAP", [])
    monkeypatch.setattr(pipeline, "GEN", "gen")
    (tmp_path / "land").mkdir()
    (tmp_path / "vegetation").mkdir()
    pipeline.world(tmp_path / "data", tmp_path, sample=False)
    for stage in ("build", "world"):
        c = next(c for c in calls if c[2:4] == ["tools.argonia_world.terrain", stage])
        assert c[c.index("--ground") + 1] == str(frozen), stage
    for mod in ("vegetation", "creatures"):
        c = next(c for c in calls if c[2] == f"tools.argonia_world.{mod}" and c[3] == "build")
        assert c[c.index("--ground") + 1] == str(frozen), mod


def test_stage_runs_once_per_key_and_records_its_time(tmp_path, monkeypatch):
    """0037: a stage reruns only when the key of its inputs moved or an output is missing."""
    monkeypatch.setattr(pipeline, "STAGE_DIR", tmp_path / "stages")
    out = tmp_path / "o"
    with pipeline.stage("s", "k1", out) as st:
        assert st.run
        out.write_text("x")
    assert pipeline.stage_known("s", "k1", out) == "skip"
    assert pipeline.stage_known("s", "k2", out) == "run"      # an input moved
    out.unlink()
    assert pipeline.stage_known("s", "k1", out) == "run"      # an output is gone
    assert pipeline.stage_known("s", None) == "run"           # unkeyed stages always run
    with pytest.raises(RuntimeError):
        with pipeline.stage("f", "k1"):
            raise RuntimeError
    assert not (tmp_path / "stages" / "f.key").exists()       # a failed stage leaves no key
    assert [r[:2] for r in pipeline.TIMES[-1:]] == [("s", "run")]


def test_files_key_names_its_inputs(tmp_path):
    a = tmp_path / "a"
    a.write_text("1")
    k = pipeline._files_key("p", files=[a])
    assert k == pipeline._files_key("p", files=[a])
    a.write_text("2")
    assert k != pipeline._files_key("p", files=[a])
    assert k != pipeline._files_key("q", files=[a])


# lane 1.15-r6-stamp-walk (owner #42): a stage stamp covers every module its entry imports and every table they read
def _expected(entry: str) -> tuple[set, set]:
    """An independent line-based walk (regex over `from tools.argonia_world.<pkg>[.<mod>] import a, b` and `import`
    lines), descending as the stamp does: through the stage packages, not past a top-level module."""
    import re
    seen, todo = set(), [entry]
    while todo:
        m = todo.pop()
        f = pipeline._mod_file(m)
        if f is None or f in seen:
            continue
        seen.add(f)
        if m.count(".") == 2 and m.startswith("tools.argonia_world."):
            continue
        todo += [".".join(m.split(".")[:i]) for i in range(1, m.count(".") + 1)]
        for base, names in re.findall(r"^\s*from (tools\.\S+) import \(?([\w ,]+)", f.read_text(), re.M):
            todo += [base, *(f"{base}.{n.split(' as ')[0].strip()}" for n in names.split(","))]
        todo += re.findall(r"^\s*import (tools\.[\w.]+)", f.read_text(), re.M)
    return seen, set(pipeline.sql_tables(seen))


@pytest.mark.parametrize("stage", sorted(pipeline.STAGE_ENTRY))
def test_stamp_covers_the_stage_imports_and_tables(stage):
    files, tables = pipeline.stage_cover(stage)
    want_files, want_tables = _expected(pipeline.STAGE_ENTRY[stage])
    want_tables -= pipeline.STAGE_WRITES.get(stage, set())  # a table the stage writes is its output, not its key
    assert want_files - set(files) == set(), f"{stage}: imported but not in the stamp"
    assert want_tables - set(tables) == set(), f"{stage}: read but not in the stamp"


def test_ground_stamp_covers_the_incident():
    files, tables = pipeline.stage_cover("ground")
    names = {str(f.relative_to(pipeline.ROOT)) for f in files}
    assert {"tools/argonia_world/routes/shape.py", "tools/argonia_world/terrain/cellwater.py"} <= names
    assert {"road", "road_point", "cell_water", "hydrology_reach"} <= set(tables)


def test_walk_is_stable_and_sees_a_new_import(tmp_path):
    for stage in pipeline.STAGE_ENTRY:
        assert pipeline.walk_imports(pipeline.STAGE_ENTRY[stage]) == pipeline.walk_imports(pipeline.STAGE_ENTRY[stage])
    pkg = tmp_path / "tools" / "argonia_world" / "demo"
    pkg.mkdir(parents=True)
    for d in (tmp_path / "tools", tmp_path / "tools" / "argonia_world", pkg):
        (d / "__init__.py").write_text("")
    (pkg / "a.py").write_text("def f():\n    from tools.argonia_world.demo import b\n")
    (pkg / "b.py").write_text("from .c import g\n")
    (pkg / "c.py").write_text("g = 'SELECT * FROM road'\n")
    got = {f.name for f in pipeline.walk_imports("tools.argonia_world.demo.a", tmp_path)}
    assert {"a.py", "b.py", "c.py"} <= got


def test_code_bytes_ignores_comments_and_docstrings_not_code(tmp_path):
    f = tmp_path / "m.py"
    f.write_text('"""doc"""\nK = 1  # c\n\ndef g():\n    """d"""\n    return K\n')
    base = pipeline._code_bytes(f)
    f.write_text('"""other doc"""\n# new comment\nK   =   1\n\ndef g():\n    # x\n    return K\n')
    assert pipeline._code_bytes(f) == base
    f.write_text('"""doc"""\nK = 2  # c\n\ndef g():\n    """d"""\n    return K\n')
    assert pipeline._code_bytes(f) != base
    f.write_text("def (:\n")
    assert pipeline._code_bytes(f) == b"def (:\n"
    (tmp_path / "t.txt").write_text("# a")
    assert pipeline._code_bytes(tmp_path / "t.txt") == b"# a"


def test_sync_yaml_follows_the_trees_not_a_shared_stage_key(tmp_path):
    src, dst = tmp_path / "out_yaml", tmp_path / "plugin"
    (src / "W").mkdir(parents=True)
    (src / "W" / "RecordData.yaml").write_text("Position: 1, 2, 4631.89\n")
    assert pipeline.sync_yaml(src, dst)                      # no plugin/ yet: copied
    assert not pipeline.sync_yaml(src, dst)                  # equal: left alone
    (dst / "W" / "RecordData.yaml").write_text("Position: 1, 2, 4631.53\n")  # another tree's build moved out/ on
    assert pipeline.sync_yaml(src, dst)                      # stale: brought level whatever any stage key says
    assert (dst / "W" / "RecordData.yaml").read_text() == "Position: 1, 2, 4631.89\n"


def test_terrain_stamp_walk_misses_the_weather_tables_and_reaches_the_shells():
    """Lane storm-grey: a weather colour change must not re-key the land pass (terrain imports regions.shells, not api)."""
    walked = {str(f.relative_to(pipeline.ROOT)) for f in pipeline.walk_imports(pipeline.STAGE_ENTRY["terrain"])}
    assert "tools/argonia_world/regions/shells.py" in walked
    assert "tools/argonia_world/regions/api.py" not in walked
    assert "tools/argonia_world/regions/classify.py" not in walked


def test_ground_stamp_walk_misses_place_build_and_reaches_ground_seat():
    """Lane claywater-reseat: an edit of place_build.py must not re-key the land pass (terrain and routes import ground_seat)."""
    for stage in ("ground", "terrain"):
        walked = {str(f.relative_to(pipeline.ROOT)) for f in pipeline.walk_imports(pipeline.STAGE_ENTRY[stage])}
        assert "tools/argonia_world/place_build.py" not in walked, stage
    assert "tools/argonia_world/ground_seat.py" in walked
