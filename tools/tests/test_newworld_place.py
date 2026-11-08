"""nw-02 step 8 placer: the rotation conventions the seating and the open-side rule rest on."""
import math

import numpy as np

from tools.navmesh.placed import rotation
from tools.newworld.place.place import tilt_rot


def test_tilt_tips_the_up_axis_down_the_slope_by_theta():
    for gx, gy, theta in ((0.3, 0.0, 10), (0.0, -0.5, 20), (0.4, 0.4, 7.5), (-1.2, 0.3, 30)):
        rx, ry = tilt_rot(theta, gx, gy)
        up = rotation(rx, ry, 1.234) @ np.array([0.0, 0.0, 1.0])  # yaw does not move the up axis
        assert math.isclose(math.degrees(math.acos(up[2])), theta, abs_tol=1e-6)
        down = np.array([-gx, -gy]) / math.hypot(gx, gy)
        assert np.allclose(up[:2] / np.linalg.norm(up[:2]), down, atol=1e-6)


def test_flat_ground_stays_upright():
    assert tilt_rot(0.0, 0.5, 0.5) == (0.0, 0.0)
    assert tilt_rot(10.0, 0.0, 0.0) == (0.0, 0.0)


def test_yaw_is_clockwise_so_the_open_side_lands_uphill():
    # a mesh open towards azimuth a (CCW from +X) placed with rz = a - uphill faces its open side uphill
    for a, uphill in ((180.0, 30.0), (-90.0, 200.0), (87.0, -45.0)):
        rz = math.radians((a - uphill) % 360)
        v = rotation(0.0, 0.0, rz) @ np.array([math.cos(math.radians(a)), math.sin(math.radians(a)), 0.0])
        got = math.degrees(math.atan2(v[1], v[0]))
        assert abs((got - uphill + 180) % 360 - 180) < 1e-6
