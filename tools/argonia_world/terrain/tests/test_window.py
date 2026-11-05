"""L2: the --rows/--cols window of `terrain build` and its refusal as the province's terrain."""
import pytest

from tools.ArgoniaGen import pipeline
from tools.argonia_world.terrain import __main__ as T
from tools.argonia_world.terrain import build as B
from tools.argonia_world.terrain import generate as G
from tools.argonia_world.terrain.grid import Sources


def test_window_cells():
    rng = (-60, -50, 40, 30)
    assert T.window_cells("-48:-46", None, rng) == (-60, -48, 40, -46)
    assert T.window_cells("-48:-46", "3:5", rng) == (3, -48, 5, -46)
    assert T.window_cells(None, None, rng) is None
    with pytest.raises(SystemExit):
        T.window_cells("-46:-48", None, rng)


def test_window_equals_whole_rows(tmp_path):
    """Two rows built alone equal the same rows of a build of the whole sample window (byte for byte)."""
    src = Sources.load()
    x0, y0, x1, y1 = (-1, 0, 1, 2)
    from tools.argonia_world import db
    from tools.argonia_world.terrain import material as M
    w = db.open()
    mat = M.Material(src, M.Water.load(w, src.pad), M.Regions.load(w, src.pad, src.n))
    B.build(src, mat, tmp_path / "whole", cells=(x0, y0, x1, y1))
    B.build(src, mat, tmp_path / "win", cells=(x0, y0 + 1, x1, y0 + 2))
    for cy in (1, 2):
        f = f"cy{cy:+04d}.jsonl.gz"
        assert (tmp_path / "whole/land" / f).read_bytes() == (tmp_path / "win/land" / f).read_bytes()


def test_windowed_dir_is_refused(tmp_path):
    (tmp_path / "terrain.stamp").write_text("k")
    assert pipeline._stamp_holds(tmp_path / "terrain.stamp", "k")
    B.mark_window(tmp_path, "0,0,1,1")
    assert B.is_window(tmp_path)
    assert not pipeline._stamp_holds(tmp_path / "terrain.stamp", "k")


def test_scratch_generate_never_writes_db(tmp_path):
    assert G.is_province_out(None) and G.is_province_out(G.OUT)
    assert not G.is_province_out(tmp_path)
