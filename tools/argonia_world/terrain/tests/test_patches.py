"""L2 (lane 1.15-r4-claywater): a terrain_patch pad is flat at its ground's mean inside its disc and eases back; a
bowl sits depth_m under its cell's water; a pad's ltex rules its disc. On synthetic rows over a sloped ground."""
import numpy as np

from tools.argonia_world import skyrim_units as su
from tools.argonia_world.terrain import patches

S = su.PROVINCE_SAMPLE_M


def _ground():
    yy, xx = np.mgrid[0:60, 0:60]
    return (10.0 + 0.2 * xx * S).astype(np.float32)  # a 20 % slope east


def _rows(**kw):
    r = {"id": "p", "kind": "pad", "x_m": 30 * S, "y_m": 30 * S, "radius_m": 4.0, "blend_m": 3.0, "rise_m": None,
         "depth_m": None, "ltex_edid": "LDirtPath01"}
    r.update(kw)
    return [r]


def test_pad_is_flat_at_its_mean_and_blends_out():
    g = _ground()
    p = patches.Patches.from_rows(_rows(), g, 0, lambda x, y: None)
    out = g.astype(np.float64).copy()
    p.apply(out, 0, 0)
    yy, xx = np.mgrid[0:60, 0:60]
    d = np.hypot(yy - 30, xx - 30) * S
    inside = out[d <= 4.0]
    assert np.ptp(inside) < 1e-6 and abs(inside.mean() - g[30, 30]) < 0.3
    far = d > 7.0 + S
    assert np.allclose(out[far], g[far])


def test_bowl_sits_under_the_water():
    g = _ground()
    p = patches.Patches.from_rows(_rows(kind="bowl", depth_m=2.5, blend_m=None, ltex_edid=None), g, 0,
                                  lambda x, y: g[30, 30] + 1.0)
    out = g.astype(np.float64).copy()
    p.apply(out, 0, 0)
    assert abs(out[30, 30] - (g[30, 30] + 1.0 - 2.5)) < 1e-3
    assert (out <= g + 1e-9).all()  # a bowl never raises


def test_pad_paints_its_disc():
    g = _ground()
    p = patches.Patches.from_rows(_rows(), g, 0, lambda x, y: None)
    w = np.zeros((60, 60, 3), np.float32)
    w[..., 0] = 1.0
    p.paint(w, 0, 0, {"LDirtPath01": 2})
    assert w[30, 30, 2] == 1.0 and w[30, 30, 0] == 0.0 and w[0, 0, 0] == 1.0


def test_old_key_only_rows_are_never_applied():
    p = patches.Patches.from_rows([{"id": "patch.bed-cut.x", "kind": None}], _ground(), 0, lambda x, y: None)
    assert len(p) == 0


def test_pad_stands_its_freeboard_over_the_wettest_cell_under_its_disc():
    """Lane 1.15-r6-claywater-water: Claywater's common stood 0.52 m over its river and the quest-board marker 0.08 m
    on the bank's slope. A pad by the water clears the highest cell water its disc touches by PAD_FREEBOARD_M; a pad
    already higher keeps its mean; a pad over dry cells keeps its mean."""
    g = _ground()
    mean = patches.Patches.from_rows(_rows(), g, 0, lambda x, y: None).items[0].level
    wet = lambda x, y: mean if x > 30 * S + 3.0 else None  # only the rim east of the centre is in a wet cell
    assert patches.Patches.from_rows(_rows(), g, 0, wet).items[0].level == round(mean + patches.PAD_FREEBOARD_M, 3)
    low = lambda x, y: mean - 5.0
    assert patches.Patches.from_rows(_rows(), g, 0, low).items[0].level == mean
