"""routes/shape.py: a road laid into synthetic ground meets Skyrim.esm's measured profile (L2)."""
import numpy as np

from tools.argonia_world.routes import shape as S


def _ground(n=200, rise=0.0, bumps=0.0):
    y, x = np.mgrid[0:n + 1, 0:n + 1].astype(np.float64)
    return x * rise * S.MPP + bumps * np.sin(x / 3.0) * np.cos(y / 5.0)


def _road(n=200):
    return [(np.array([[10.0, n / 2], [n - 10.0, n / 2]]), 4.5 / S.MPP)]  # a 5 m road with 2 m shoulders


def test_grade_limit_is_lipschitz():
    z = np.array([0, 5, 0, 10, 10, 2, 30], float)
    g = S.grade_limit(z, 1.0, 0.2)
    assert np.abs(np.diff(g)).max() <= 0.2 + 1e-9


def test_grade_within_never_cuts_past_the_cap():
    z = np.concatenate([np.zeros(20), np.linspace(0, 6, 10), np.full(20, 6.0)])  # a 6 m bank in 10 samples
    g = S.grade_within(z.copy(), z, 1.0, 0.2)
    assert np.abs(g - z).max() <= S.MAX_CUT_M + 1e-9
    gentle = np.linspace(0, 3, 50)
    assert np.abs(np.diff(S.grade_within(gentle + 0.3 * np.sin(np.arange(50)), gentle, 1.0, 0.2))).max() <= 0.2 + 1e-9


def _flooded(n=120, level=2.0, bed=-3.0):
    """A 5 m deep lake over the whole window, one level, a road across it."""
    h = np.full((n + 1, n + 1), bed)
    lo, hi = np.full(h.shape, -np.inf), np.full(h.shape, level - 0.3)
    role = np.ones(h.shape, np.uint8)
    vl = np.full(h.shape, level)
    return h, lo, hi, role, vl


def test_reach_crossing_is_a_ford():
    n = 120
    h, lo, hi, role, vl = _flooded(n)
    road = _road(n)
    reach = np.zeros(h.shape, bool)
    reach[:, 55:66] = True  # a stream across the road
    dc = S.dry_corridor(road, lo, hi, role, vl, vl, reach)
    assert dc["ford"].any()
    h = np.minimum(np.maximum(h, lo), hi)
    d = 2.0 - h[n // 2, 56:65]
    assert (d > 0).all() and d.max() <= S.FORD_M + 1e-6, d


def test_step_channel_under_a_road_is_capped_at_the_ford_depth():
    n = 120
    h, lo, hi, role, vl = _flooded(n)
    road = _road(n)
    chan = np.zeros(h.shape, bool)
    chan[:, 58:61] = True  # a step's channel across the road, its bed 2 m under the level
    hi[chan] = 0.0
    h[chan] = 0.0
    dc = S.dry_corridor(road, lo, hi, role, vl, vl, np.zeros(h.shape, bool), keep=chan)
    h = np.minimum(np.maximum(h, lo), hi)
    d = 2.0 - h[n // 2, 58:61]
    assert np.allclose(d, S.FORD_M), d
    assert h[5, 59] == 0.0  # off the corridor the channel keeps its bed
    assert dc["ford"][n // 2, 59]


def test_bridge_deck_stands_at_the_raised_corridor():
    """A crossing on a causeway: the deck top is the corridor's height (the higher end), the seats level with it,
    no seat sample under the causeway, the step's channel between untouched."""
    n = 120
    y, x = np.mgrid[0:n + 1, 0:n + 1].astype(np.float64)
    chan = (x >= 58) & (x <= 62)
    h = np.where(x < 60, 60.0, 56.0)  # the land under a step's two levels
    road = [(np.array([[10.0, n / 2], [n - 10.0, n / 2]]), 4.5 / S.MPP)]
    cor = S.corridor(h.shape, road)
    lo, hi = np.full(h.shape, -np.inf), np.full(h.shape, np.inf)
    hi[chan] = 55.0
    causeway = np.where(x < 60, 61.1, 56.2)  # dry_corridor's top over each cell's water
    lo[cor & ~chan] = causeway[cor & ~chan]
    hc = np.minimum(np.maximum(h, lo), hi)
    seats = [{"bridge": "b", "end": k, "at_m": [cx * S.MPP, n / 2 * S.MPP], "z_m": None, "heading": 90.0,
              "centre_m": [60 * S.MPP, n / 2 * S.MPP], "yaw": 0.0, "from_m": -0.3, "to_m": 4.0, "half_width_m": 3.0}
             for k, cx in enumerate((56.0, 64.0))]
    decks = S.bridge_decks(hc, seats)
    assert decks[0]["deck_m"] == 61.1, decks
    lo0 = lo.copy()
    bs = S.bridge_seats(seats, lo, hi, keep=chan, corridor_m=cor, h=hc)
    f = np.minimum(np.maximum(hc, lo), hi)
    for cx in (54, 56, 64, 66):
        assert abs(f[n // 2, cx] - 61.1) < 1e-9, (cx, f[n // 2, cx])
    seat = bs["seated"]
    assert (f[seat] >= lo0[seat] - 1e-9).all()  # never under the causeway
    assert (f[chan] == hc[chan]).all() and not seat[chan].any()  # the channel untouched
    g = np.abs(np.diff(f[n // 2, 66:])) / S.MPP  # the lower side eased up to the deck
    assert g.max() <= S.GRADE_MAX + 1e-6, g.max()


def test_seat_census_reds_a_seat_off_its_deck():
    from tools.argonia_world.routes import census as K
    h = np.full((101, 101), 5.0)
    h[:, 61:] = 5.5
    seats = [{"bridge": "b", "end": k, "at_m": [cx * S.MPP, 50 * S.MPP], "z_m": 5.0, "heading": 90.0,
              "from_m": -0.3, "to_m": 4.0, "half_width_m": 3.0} for k, cx in enumerate((40.0, 60.0))]
    out = K.seat_census(h, seats)
    assert not out[0]["red"] and out[1]["red"] and out[1]["off_max_m"] == 0.5, out


def test_deck_span_lies_between_the_seats():
    seats = [{"bridge": "b", "end": k, "at_m": [cx * S.MPP, 50 * S.MPP], "from_m": -0.3, "half_width_m": 3.0}
             for k, cx in enumerate((50.0, 60.0))]
    m = S.deck_span((101, 101), seats)
    assert m[50, 52:59].all() and not m[50, 51] and not m[50, 59] and not m[40, 55]  # inset SEAT_UNDER_SAMPLES


def test_bridge_on_a_climbing_road_seats_the_whole_axis():
    """The road climbs away from the crossing: the deck is the seat axis's highest ground, and after the seats the
    ground along each seat (0.3 m under the deck to 4 m beyond) stands at the deck top (the census's seat bar)."""
    from tools.argonia_world.routes import census as K
    n = 120
    y, x = np.mgrid[0:n + 1, 0:n + 1].astype(np.float64)
    chan = (x >= 58) & (x <= 62)
    h = 60.0 + 0.6 * np.abs(x - 60) * S.MPP  # climbing 0.6 m a metre both ways from the channel
    lo, hi = np.full(h.shape, -np.inf), np.full(h.shape, np.inf)
    road = [(np.array([[10.0, n / 2], [n - 10.0, n / 2]]), 4.5 / S.MPP)]
    seats = [{"bridge": "b", "end": k, "at_m": [cx * S.MPP, n / 2 * S.MPP], "z_m": None, "heading": 90.0,
              "centre_m": [60 * S.MPP, n / 2 * S.MPP], "yaw": 0.0, "from_m": -0.3, "to_m": 4.0, "half_width_m": 3.0}
             for k, cx in enumerate((55.0, 65.0))]
    S.bridge_decks(h, seats)
    S.bridge_seats(seats, lo, hi, keep=chan, corridor_m=S.corridor(h.shape, road), h=h)
    f = np.minimum(np.maximum(h, lo), hi)
    out = K.seat_census(f, seats)
    assert not any(q["red"] for q in out), out


def test_bridge_whose_ends_differ_by_4_m_ramps_the_lower_end():
    """One end's corridor 4 m over the other's: the deck is the higher end's, the lower seat a ramp up to it, both
    seats on the census's bilinear axis within the bar, the ground under the deck clear of it."""
    from tools.argonia_world.routes import census as K
    n = 120
    y, x = np.mgrid[0:n + 1, 0:n + 1].astype(np.float64)
    chan = (x >= 58) & (x <= 62)
    h = np.where(x < 60, 64.0, 60.0)
    h[chan] = 55.0
    lo, hi = np.full(h.shape, -np.inf), np.full(h.shape, np.inf)
    hi[chan] = 55.0
    road = [(np.array([[10.0, n / 2], [n - 10.0, n / 2]]), 4.5 / S.MPP)]
    seats = [{"bridge": "b", "end": k, "at_m": [cx * S.MPP, n / 2 * S.MPP], "z_m": None, "heading": 90.0,
              "centre_m": [60 * S.MPP, n / 2 * S.MPP], "yaw": 0.0, "from_m": -0.3, "to_m": 4.0, "half_width_m": 3.0}
             for k, cx in enumerate((55.0, 65.0))]
    decks = S.bridge_decks(h, seats)
    assert decks[0]["deck_m"] == 64.0
    S.bridge_seats(seats, lo, hi, keep=chan | S.deck_span(h.shape, seats), corridor_m=S.corridor(h.shape, road), h=h,
                   keep_ch=chan)
    from tools.argonia_world.terrain.generate import limit
    f, _ = limit(np.minimum(np.maximum(h, lo), hi), lo, hi, 6.8)
    out = K.seat_census(f, seats)
    assert not any(q["red"] for q in out), out
    assert (f[n // 2, 57:64] <= 64.0 - S.DECK_CLEAR_M + 1e-9).all(), f[n // 2, 55:66]
    g = np.abs(np.diff(f[n // 2, 68:])) / S.MPP  # the lower road eased up to the deck
    assert g.max() <= S.GRADE_MAX + 1e-6, g.max()
