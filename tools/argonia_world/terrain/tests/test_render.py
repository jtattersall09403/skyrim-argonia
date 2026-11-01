"""L2: the renderer draws hillshade and cell water from a synthetic ground; the fixture's steps from levels."""
import numpy as np

from tools.argonia_world.terrain import cellwater as cw
from tools.argonia_world.terrain import png, render


def _water():
    lev = np.full((cw.C, cw.C), np.nan)
    lev[cw.C - 1, 0] = 5.0  # cell (CX0, CY0)
    lev[cw.C - 1, 1] = 2.0  # its east neighbour, 3 m lower
    typ = np.where(np.isnan(lev), -1, 2).astype(np.int8)
    wet = np.zeros((cw.N + 1, cw.N + 1), bool)
    wet[cw.N - 20:cw.N - 10, 0:64] = True  # a channel across the shared edge
    return cw.CellWater(lev, typ, cw.derive_steps(lev, wet))


def test_steps_from_levels():
    w = _water()
    assert len(w.steps) == 1
    s = w.steps[0]
    assert (s.cx, s.cy, s.edge, s.upper_m, s.lower_m) == (cw.CX0, cw.CY0, "e", 5.0, 2.0)
    assert (s.cross_lo, s.cross_hi) == (11, 20)


def test_render_window(tmp_path):
    w = _water()
    g = np.full((cw.N + 1, cw.N + 1), 10.0, np.float32)
    g[cw.N - 20:cw.N - 10, 0:64] = 0.0
    win = render.window(g, w, (cw.CX0, cw.CY0, cw.CX0 + 1, cw.CY0))
    out = render.render(win, tmp_path / "w.png", layers=[])
    img = png.read(tmp_path / "w.png")
    assert img.shape == (33, 65, 3)
    assert out["wet_samples"] == 10 * 64
    assert (img[cw.Q - 15, cw.Q] == render.STEP_RGB).all()  # the step drawn on the east edge
