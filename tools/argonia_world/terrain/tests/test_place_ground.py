"""L2: a built place's ground edit (place_ground.py) is a ceiling bowl: flat at its floor, rising on its side, never
raising the ground, and placed by province metres in grid space."""
import numpy as np

from tools.argonia_world import skyrim_units as su
from tools.argonia_world.terrain.place_ground import Edits


def test_bowl_is_a_ceiling_with_a_flat_floor_and_a_side():
    s = su.PROVINCE_SAMPLE_M
    e = Edits([(10.0, 10.0, 5.0, 2 * s, 0.5)], pad=4)  # column 10, row 10 of the province; the grid pads by 4
    out = np.full((40, 40), 10.0)
    e.apply(out, 0, 0)
    assert out[14, 14] == 5.0 and out[14, 16] == 5.0  # the floor over the flat radius
    assert out[14, 18] == 5.0 + (4 * s - 2 * s) * 0.5  # the side rises 0.5 m per m beyond it
    assert out[14, 39] == 10.0 and out.max() == 10.0  # far away, and never above the ground
    low = np.full((40, 40), 1.0)
    e.apply(low, 0, 0)
    assert (low == 1.0).all()  # ground below the bowl stays


def test_a_window_offset_sees_the_same_bowl():
    e = Edits([(10.0, 10.0, 5.0, 3.0, 0.5)], pad=4)
    whole = np.full((40, 40), 10.0)
    e.apply(whole, 0, 0)
    part = np.full((10, 10), 10.0)
    e.apply(part, 10, 12)
    assert np.array_equal(part, whole[10:20, 12:22])
