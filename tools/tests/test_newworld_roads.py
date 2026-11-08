"""The road tracer's pieces on small synthetic images: gap bridging, snapping to places, class from dash pattern."""
import numpy as np

from tools.newworld import roads as R


def test_bridge_joins_facing_ends_across_hidden_gap():
    sk = np.zeros((40, 120), bool)
    sk[20, 5:45] = True
    sk[20, 75:115] = True
    hidden = np.zeros_like(sk)
    hidden[:, 45:75] = True                     # a river
    out, bridges = R.bridge(sk, hidden)
    assert len(bridges) == 1 and out[20, 45:75].all()


def test_bridge_refuses_long_gap_over_open_land():
    sk = np.zeros((40, 120), bool)
    sk[20, 5:45] = True
    sk[20, 75:115] = True
    _, bridges = R.bridge(sk, np.zeros_like(sk))
    assert bridges == []


def test_snap_end_to_glyph_and_junction_only_inside():
    syms = [{"px": 50.0, "py": 50.0, "glyph": "settlement"}]
    assert R.snap_places([(62.0, 50.0)], syms, [1]) == [0]       # end 12 px off: snaps
    assert R.snap_places([(62.0, 50.0)], syms, [3]) == [None]    # junction beside the glyph: stays
    assert R.snap_places([(80.0, 50.0)], syms, [1]) == [None]


def test_class_from_dash_pattern():
    n = 200
    skip = np.zeros(n, bool)
    solid = np.ones(n, bool)
    dashed = (np.arange(n) % 11) < 7
    assert not R.classify(solid, skip).any()
    assert R.classify(dashed, skip).all()


def test_densify_and_resample_spacing():
    pts = R.densify([[0, 0], [10, 0]])
    assert max(abs(b[0] - a[0]) for a, b in zip(pts, pts[1:])) <= R.STEP_PX
    path = [(0, x) for x in range(31)]
    out = R.smooth_resample(path)
    assert len(out) == 11 and abs(out[-1][0] - 30.5) < 1e-6
