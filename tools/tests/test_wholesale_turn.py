"""The wholesale carry turns points the way the fit and the ground carry do (geom.Xf: clockwise yaw), so a turned
place's pieces stand on the relief carried under them."""
import math

from tools.places.draft import geom, srcnav


def test_srcnav_turn_matches_xf():
    place = {"fit": {"pivot": [100.0, 200.0], "anchor": [5000.0, -7000.0], "rot_deg": 90.0}, "wholesale": {"offset": 10}}
    ours, _ = srcnav._transform(place)
    xf = geom.Xf((100.0, 200.0), (5000.0, -7000.0), math.radians(90.0))
    for p in [(300.0, 200.0), (100.0, 650.0), (-40.0, -80.0)]:
        x, y, z = ours(*p, 0.0)
        ex, ey = xf.pt(*p)
        assert math.isclose(x, ex, abs_tol=1e-6) and math.isclose(y, ey, abs_tol=1e-6)


def test_wholesale_turn_matches_xf():
    src = open(__file__.replace("tests/test_wholesale_turn.py", "places/draft/wholesale.py")).read()
    assert "dx * c - dy * s" not in src, "wholesale turns points anticlockwise: not as geom.Xf"
