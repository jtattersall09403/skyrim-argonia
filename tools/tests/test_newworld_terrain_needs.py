"""The bank beside a place and the needs judged behind it, on small synthetic ground."""
import numpy as np

from tools.newworld import terrain_clearance as tcl
from tools.newworld import terrain_needs as tn
from tools.newworld import terrain_shape as ts

N = 97


def _grid():
    return ts.Grid(rows=N, cols=N, p0x=0.0, p0y=0.0)


def _rec(g, need, r, i=48, j=48):
    px, py = g.px(i, j)
    return {"need": need, "radius_m": r, "px": float(px), "py": float(py)}


def _shore(level=280.0, water_cols=40):
    """Water on the west, ground level to the water's edge at `level` units: (h, water_s, sd_m)."""
    h = np.full((N, N), level, np.float32)
    ws = np.zeros((N, N), bool)
    ws[:, :water_cols] = True
    h[ws] = -40.0
    h[:, water_cols - 1] = -8.0                              # the bed at the shore is shallow
    m = ts.STEP / ts.U
    sd = np.tile(((np.arange(N) - water_cols + 0.5) * m).astype(np.float32), (N, 1))
    return h, ws, sd


def test_place_bank_eases_the_band_and_keeps_the_ground_behind():
    h, ws, sd = _shore()
    before = h.copy()
    assert tcl.shore_steep(h)["over_walk"] == 1.0            # 4 m of pad standing at the waterline
    shaped = np.zeros((N, N), bool)
    shaped[:60] = True
    bank = np.ones((N, N), np.uint8)
    bank[80:] = 0                                            # a river's bank is left
    leave = np.zeros((N, N), bool)
    leave[50:55] = True                                      # a road's bed
    out = tcl.place_banks(h, ws, sd, bank, shaped, leave)
    band = tcl.bank_band(ws)
    assert band[:, 40:42].all() and not band[:, 42:].any() and tcl.BANK_BAND_M == 2 * ts.STEP / ts.U
    free = np.r_[0:50, 55:60]
    assert out["in_places_bands"] == 2 * len(free)
    assert (h[ws] == before[ws]).all() and ((h > 0) == (before > 0)).all()          # the waterline does not move
    assert (h[free][:, 42:] == before[free][:, 42:]).all()   # behind the band the pad is as shaped
    rise = np.diff(np.c_[np.full(len(free), tcl.SHORE_M * tcl.U), h[free][:, 40:42]], axis=1)
    assert (h[free][:, 40] < 100).all() and (rise <= tcl.PLACE_BANK * ts.STEP + 1e-3).all()
    assert tcl.shore_steep(h[:50])["over_walk"] == 0.0       # every waterline triangle is walked
    assert (h[50:55] == before[50:55]).all() and (h[80:] == before[80:]).all()
    # past the places' needs the natural bank bounds the ground: Hjaalmarch's profile, not the pad's level
    assert (h[60:80, 40] <= 48).all() and (h[60:80, 41] < 110).all()


def test_pad_is_judged_behind_the_bank():
    g = _grid()
    h, ws, sd = _shore()
    tcl.place_banks(h, ws, sd, np.ones((N, N), np.uint8), np.ones((N, N), bool))
    ok, why = tn.judge(h, g, _rec(g, "flat-pad", 20.0, 48, 46))
    assert ok and why == "slope p90 0.0 deg"                 # the 31-degree bank is not the pad's slope
    tilt = h + np.where(~ws, np.arange(N)[None, :] * ts.STEP * np.tan(np.radians(12.0)), 0).astype(np.float32)
    ok, why = tn.judge(tilt, g, _rec(g, "flat-pad", 20.0, 48, 46))
    assert not ok and why.startswith("slope p90 1")          # a tilted pad still fails on its own ground
    spit = h.copy()
    spit[:, 45:] = -40.0                                     # five samples of land between two waters
    ok, why = tn.judge(spit, g, _rec(g, "flat-pad", 20.0, 48, 42))
    assert not ok and why.startswith("no room behind the bank")
    ok, why = tn.judge(np.full((N, N), -40.0, np.float32), g, _rec(g, "flat-pad", 20.0))
    assert not ok and why == "no land in the footprint"


def test_rise_is_judged_behind_the_bank():
    g = _grid()
    h, ws, sd = _shore(level=70.0)
    ts.rise(h, ws, g, 48.0, 46.0, 30.0)
    tcl.place_banks(h, ws, sd, np.ones((N, N), np.uint8), np.ones((N, N), bool))
    ok, why = tn.judge(h, g, _rec(g, "rise", 30.0, 48, 46))
    assert ok, why                                           # the top stands over the land round it, bank left out
    islet = np.full((N, N), -40.0, np.float32)
    islet[45:52, 45:52] = 400.0                              # a rock seven samples across: all but its middle is bank
    islet[:, 80:] = 70.0
    ok, why = tn.judge(islet, g, _rec(g, "rise", 30.0))
    assert not ok and why.startswith("no room behind the bank")


def test_shore_access_is_judged_at_the_waterline_and_a_buried_landing_is_cut_again():
    g = _grid()
    h, ws, sd = _shore()
    tcl.place_banks(h, ws, sd, np.ones((N, N), np.uint8), np.ones((N, N), bool))
    rec = _rec(g, "shore-access", 30.0, 48, 46)
    ok, why = tn.judge(h, g, rec)
    assert not ok and why.startswith("gentlest bank")        # the whole waterfront is a 31-degree bank
    leave = np.zeros((N, N), bool)
    leave[:40] = True
    before = h.copy()
    ts.shore_access(h, ws, g, 48.0, 46.0, 30.0, leave=leave)
    assert (h[:40] == before[:40]).all() and (h[45:52, 40:44] < before[45:52, 40:44]).all()
    ok, why = tn.judge(h, g, rec)
    assert ok, why
    ok, why = tn.judge(np.full((N, N), 70.0, np.float32), g, rec)
    assert not ok and why == "no water within reach"
