"""Hang points on synthetic trees, and a hanging thing posed onto a placed tree."""
import math

import numpy as np

from tools.newworld.dressing import hang_points as hp
from tools.newworld.dressing import place as dp


def box(x0, x1, y0, y1, z0, z1):
    """A closed box as (12, 3, 3) triangles, outward faces."""
    v = np.array([[x, y, z] for z in (z0, z1) for y in (y0, y1) for x in (x0, x1)], float)
    f = [(0, 2, 1), (1, 2, 3), (4, 5, 6), (5, 7, 6), (0, 1, 4), (1, 5, 4), (2, 6, 3), (3, 6, 7),
         (0, 4, 2), (2, 4, 6), (1, 3, 5), (3, 7, 5)]
    return v[np.array(f)]


TRUNK = box(-20, 20, -20, 20, 0, 600)
LIMB = box(20, 300, -8, 8, 340, 360)       # a horizontal limb 20 units deep, 4.9 m up


def test_limb_underside_found():
    wood = np.concatenate([TRUNK, LIMB])
    pts = hp.find_points(wood, wood)
    assert pts and all(abs(p[2] - 340) < 0.01 and p[3] >= hp.THICK for p in pts)
    assert all(p[0] >= 20 + hp.CLEAR for p in pts)


def test_no_point_over_geometry_or_too_low():
    shelf = box(0, 320, -40, 40, 250, 255)     # something just under the limb
    wood = np.concatenate([TRUNK, LIMB])
    assert hp.find_points(wood, np.concatenate([wood, shelf])) == []
    low = box(20, 300, -8, 8, 60, 80)
    assert hp.find_points(np.concatenate([TRUNK, low]), np.concatenate([TRUNK, low])) == []


def test_thin_limb_rejected():
    thin = box(20, 300, -3, 3, 340, 343)
    wood = np.concatenate([TRUNK, thin])
    assert hp.find_points(wood, wood) == []


def test_leaf_cards_told_from_bark():
    assert hp.is_leaf({"tex": ["textures\\trees\\willowleaves.dds"], "shader": {}})
    assert not hp.is_leaf({"tex": ["textures\\trees\\willowbark01.dds"], "shader": {"two_sided": True}})
    assert hp.is_leaf({"tex": ["textures\\trees\\x.dds"], "shader": {"two_sided": True}})


def test_hang_world_posed_by_tree():
    t = {"x": 1000.0, "y": 2000.0, "z": -30.0, "rx": 0.0, "ry": 0.0, "rz": math.pi / 2, "scale": 2.0}
    w = dp.hang_world(t, [100.0, 0.0, 300.0])
    assert np.allclose(w, [1000.0, 2200.0, 570.0], atol=1e-6)
