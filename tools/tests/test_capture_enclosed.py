"""A camera under a building's porch or eave is inside its box but not inside the building (capture.enclosed)."""
import numpy as np

from tools.places import shape
from tools.places.look import capture


class _Shell:
    """A 1000 x 600 house of walls 300 high on z 0..300 with a flat roof, and a roof-only porch 400 deep to its west."""
    def __init__(self):
        pts = []
        for z in range(0, 301, 25):
            for x in range(0, 1001, 25):
                pts += [(x, 0, z), (x, 600, z)]
            for y in range(0, 601, 25):
                pts += [(0, y, z), (1000, y, z)]
        for x in range(-400, 1001, 25):
            for y in range(0, 601, 25):
                pts.append((x, y, 320))
        self.P = np.asarray(pts, float)


def _house():
    return {"id": "h", "kind": "building", "model": "m.nif", "m": np.eye(4).tolist(), "lo": [-400, 0, 0],
            "hi": [1000, 600, 330]}


def test_inside_walls_is_enclosed_under_the_porch_is_not(monkeypatch):
    monkeypatch.setattr(shape, "posed", lambda p: _Shell())
    h = _house()
    assert capture.enclosed(h, (500, 300, 160))
    assert not capture.enclosed(h, (-200, 300, 160))   # under the porch roof, open to the west
    assert capture.camera_inside((500, 300, 160), [h], 0.0) is not None
    assert capture.camera_inside((-200, 300, 160), [h], 0.0) is None


def test_no_mesh_read_keeps_the_box(monkeypatch):
    def boom(p):
        raise FileNotFoundError
    monkeypatch.setattr(shape, "posed", boom)
    assert capture.camera_inside((-200, 300, 160), [_house()], 0.0) is not None
