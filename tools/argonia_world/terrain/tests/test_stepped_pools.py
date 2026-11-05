"""L1 (lane 1.15-r6-stepped-pools-2): a hillside river keeps its pools beside a level step, as Skyrim.esm's does.

Synthetic 3 x 3 cells: the west column's water at 20 m, the rest at 10 m, the ground falling east, water beside the
step line on both sides. Skyrim.esm (probes/vanilla_hanging_edges.py): the falls face drops ~2.0 m per vertex into
the lower pool and the lower thalweg is under the lower level by vertex 6 (p50), so no lift fills the carved pool.
A road's corridor and a step bridge's seat are exempt (the causeway and the seat stand on the full lift)."""
from types import SimpleNamespace

import numpy as np

from tools.argonia_world.terrain import generate as G
from tools.argonia_world.terrain import water_field as W
from tools.argonia_world.terrain.cellwater import Q

UP, LV = 20.0, 10.0
N_ = 3 * Q + 1


def _scene():
    level = np.full((3, 3), LV)
    level[:, 0] = UP
    i = np.arange(N_)
    lo_c, hi_c = np.clip((i - 1) // Q, 0, 2), np.clip(i // Q, 0, 2)
    st = np.stack([level[a][:, b] for a in (lo_c, hi_c) for b in (lo_c, hi_c)])
    vmin, vmax = st.min(0), st.max(0)
    xx = np.mgrid[0:N_, 0:N_][1].astype(np.float64)
    h = np.where(xx <= Q, UP + 1.0 - xx * 0.02, LV + 1.0 - (xx - Q) * 0.01)
    foot = np.zeros((N_, N_), bool)
    foot[4:-4, 2:Q - 1] = True
    foot[4:-4, Q + 1:2 * Q + Q // 2] = True
    touch = np.zeros((N_, N_), bool)
    chz = np.zeros((N_, N_), bool)
    tsamp = np.full((N_, N_), G.TYPES.index("fresh"), np.int8)
    return h, foot, vmin, vmax, touch, chz, tsamp


def _run(exempt=None):
    h, foot, vmin, vmax, touch, chz, tsamp = _scene()
    h2, role, lo, hi, d = W.water_field(h, foot, vmin, vmax, touch, chz, tsamp, exempt=exempt)
    return h2, role, d, foot


def _lower_pool(foot):
    m = foot.copy()
    m[:, :Q + 1 + int(np.ceil((UP - LV) / W.WALL_GRADE)) + 1] = False
    m[:Q // 2] = m[-Q // 2:] = False
    return m


def test_carve_under_the_level_at_a_steps_foot():
    h2, role, d, foot = _run()
    m = _lower_pool(foot)[:, :Q + 8]
    assert m.any()
    assert (role[:, :Q + 8][m] == 1).all()
    assert (h2[:, :Q + 8][m] < LV).all(), float(h2[:, :Q + 8][m].max())


def test_no_lift_over_face_grade_beside_a_step():
    h2, role, d, foot = _run()
    dist, _ = G.chamfer(foot & ~d["src"], 40)
    dist = np.where(np.isfinite(dist), dist, 40.0)
    wall = W.cone(d["src"] & (d["lift"] > 0), np.where(d["src"], d["lift"], 0.0), W.WALL_GRADE)
    room = np.maximum(W.FACE_GRADE * dist, wall)
    assert (d["lift"] <= room + 1e-6).all(), float((d["lift"] - room).max())
    assert d["lift"][_lower_pool(foot)].max() < 0.05


def test_the_clipped_lines_wall_keeps_its_need():
    h2, role, d, foot = _run()
    line = h2[Q // 2:-Q // 2, Q]
    assert (line >= UP + G.FREEBOARD_M - 1e-6).all(), float(line.min())
    # it falls into the lower pool at the wall grade: within the wall's reach of the line, never a 0.6 m/sample fill
    assert h2[Q, Q + int(np.ceil((UP - LV) / W.WALL_GRADE)) + 2] < LV


def _band():
    m = np.zeros((N_, N_), bool)
    m[Q - 4:Q + 5, :] = True
    return m


def _inner(m):
    d, _ = G.chamfer(~m, 8)
    return m & (np.nan_to_num(d, nan=99.0) > 2 * W.SOFT)


def test_a_road_core_is_untouched_by_the_pool_rule():
    full = _run(exempt=np.ones((N_, N_), bool))[2]["lift"]
    kept = _run()[2]["lift"]
    road = _run(exempt=_band())[2]["lift"]
    b = _band()
    assert (full[b] > kept[b] + 0.5).any()  # the rule bites there when the road is not exempt
    core = _inner(b)  # the field's blur (SOFT) reaches a few samples over the corridor's line
    np.testing.assert_allclose(road[core], full[core], atol=1e-6)


def test_a_bridge_seat_is_untouched_by_the_pool_rule():
    mpp = G.MPP
    seats = [{"bridge": "bridge.t", "end": k, "at_m": [x * mpp, Q * mpp], "from_m": -2.0, "to_m": 6.0,
              "half_width_m": 2.0} for k, x in ((0, Q - 3), (1, Q + 3))]
    ex = G.pool_exempt((N_, N_), SimpleNamespace(roads=[], seats=seats))
    assert ex[Q, Q] and ex[Q, Q + 3 + int(6.0 / mpp)] and not ex[4, 2 * Q]
    full = _run(exempt=np.ones((N_, N_), bool))[2]["lift"]
    seat = _run(exempt=ex)[2]["lift"]
    core = _inner(ex)
    np.testing.assert_allclose(seat[core], full[core], atol=1e-6)
