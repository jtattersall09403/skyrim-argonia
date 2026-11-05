"""Lane 1.15-r6-road-profile: a road keeps Skyrim.esm's trough on a causeway's floor and through a place's pinned pad,
its lane no wider than vanilla's p95 flat width, no step or spike across it (census.profile_census), and the paint
full across the lane (material.ROAD_FULL_M) (L1/L2)."""
import numpy as np

from tools.argonia_world.routes import census as C
from tools.argonia_world.routes import shape as S
from tools.argonia_world.routes.tests.test_shape import _flooded, _road

N = 200


def _causeway():
    """A flat marsh at its water's level: dry_corridor raises the corridor, then the road pass lays the road."""
    h, lo, hi, role, vl = _flooded(N, level=2.0, bed=1.9)
    road = _road(N)
    S.dry_corridor(road, lo, hi, role, vl, vl, np.zeros(h.shape, bool))
    h = np.minimum(np.maximum(h, lo), hi)
    S.shape(h, road, None, lo, hi)
    return np.minimum(np.maximum(h, lo), hi), lo, road


def _pad():
    """A place's flat pinned pad (lo == hi) the road runs across."""
    h = np.full((N + 1, N + 1), 5.0)
    lo, hi = np.full(h.shape, -np.inf), np.full(h.shape, np.inf)
    lo[:, 60:140], hi[:, 60:140] = 5.0, 5.0
    road = _road(N)
    S.shape(h, road, None, lo, hi)
    return np.minimum(np.maximum(h, lo), hi), road


def _sampled(h, road, k=20):
    offs, pr = C.cross_profiles(h, road[0][0], step_m=10.0)
    idx = np.linspace(2, len(pr) - 3, k).astype(int)  # 20 sampled road points, off the road's ends
    return offs, pr[idx]


def test_causeway_carries_the_measured_trough():
    h, lo, road = _causeway()
    offs, pr = _sampled(h, road)
    fold4 = (pr[:, np.isclose(offs, 4.0)] + pr[:, np.isclose(offs, -4.0)])[:, 0] / 2
    lo4, hi4 = C.TROUGH_BAND[4.0]
    assert ((fold4 >= lo4 - 0.05) & (fold4 <= hi4 + 0.05)).all(), fold4
    fw = [C.flat_width(z, len(offs) // 2, C.PROFILE_DS_M) for z in pr]
    assert max(fw) <= C.VANILLA_PROFILE["flat_width_p95_m"], fw
    assert np.abs(np.diff(pr, 2, axis=1)).max() <= C.VANILLA_PROFILE["second_diff_p95"]
    assert h[N // 2, 50:150].min() >= lo[N // 2, 50:150].min() - 1e-6  # the centre stays on the dry floor


def test_pinned_pad_shows_the_trough():
    h, road = _pad()
    offs, pr = C.cross_profiles(h, road[0][0], step_m=10.0)
    on = pr[8:12]  # the road points on the pad (cols 80..120)
    fold4 = (on[:, np.isclose(offs, 4.0)] + on[:, np.isclose(offs, -4.0)])[:, 0] / 2
    assert (fold4 >= 0.15).all(), fold4
    assert h[60:140, 60:140].max() <= 5.0 + 1e-9  # the pad is never raised
    assert h[N // 2 + 10:, 60:140].min() >= 5.0 - 1e-9  # off the road the pad keeps its level


def test_profile_census_flags_a_slab():
    flat = np.zeros((N + 1, N + 1))
    r = C.profile_census(flat, _road(N))
    assert r["flat_over_share"] == 1.0 and C.profile_fails(r)
    h, _lo, road = _causeway()
    assert not C.profile_fails(C.profile_census(h, road)), C.profile_census(h, road)


def test_paint_is_full_across_the_lane():
    from tools.argonia_world.terrain import material as M
    # Skyrim.esm's road dirt holds to 5 m from the centre (probes/vanilla_road_profile.py --marsh); a 6 m lane
    assert 3.0 + M.ROAD_FULL_M >= 5.0 and M.ROAD_FULL_M + M.ROAD_BLEND_M <= 4.0 + 1e-9


def test_site_flat_crossed_by_road_is_no_slab():
    """A place's tilted pinned pad crossed by a road: the trough is cut after the pad (lane roadslab): the fold at 4 m
    is vanilla's band, the flat width inside Skyrim's p95, the pad never raised."""
    h = np.full((N + 1, N + 1), 5.0) + 0.02 * np.arange(N + 1)[None, :]
    lo, hi = np.full(h.shape, -np.inf), np.full(h.shape, np.inf)
    lo[:, 60:140], hi[:, 60:140] = h[:, 60:140], h[:, 60:140]
    base = h.copy()
    road = _road(N)
    S.shape(h, road, None, lo, hi)
    h = np.minimum(np.maximum(h, lo), hi)
    offs, pr = C.cross_profiles(h, road[0][0], step_m=10.0)
    on = pr[8:12]
    fold4 = (on[:, np.isclose(offs, 4.0)] + on[:, np.isclose(offs, -4.0)])[:, 0] / 2
    lo4, hi4 = C.TROUGH_BAND[4.0]
    assert ((fold4 >= lo4) & (fold4 <= hi4 + 0.05)).all(), fold4
    assert max(C.flat_width(z, len(offs) // 2, C.PROFILE_DS_M) for z in on) <= C.VANILLA_PROFILE["flat_width_p95_m"]
    assert (h[:, 60:140] <= base[:, 60:140] + 1e-9).all()


def test_road_end_is_square_across():
    """A road that ends (a place's centre) still reads the full trough at its last point."""
    h = np.full((N + 1, N + 1), 5.0)
    road = _road(N)
    S.shape(h, road, None)
    offs, pr = C.cross_profiles(h, road[0][0], step_m=10.0)
    assert C.flat_width(pr[-1], len(offs) // 2, C.PROFILE_DS_M) <= C.VANILLA_PROFILE["flat_width_p95_m"]
