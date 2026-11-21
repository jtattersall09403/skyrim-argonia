import pytest

from tools.places.look.verbs import land_ops

PLACE = {"fit": {"anchor": [0.0, 0.0], "patch_max": 105.0}, "radius_m": 120}


def test_land_raises_a_bounded_eased_mound_as_land_patches_against_the_rows():
    files = {"place": PLACE, "land": [{"cell": [0, 0], "verts": [[2, 2, 10.0]]}]}
    ops = land_ops(files, None, ["256,256", "300", "40"], {"why": "a mound under legs"})
    assert all(op["op"] == "land.patch" for op in ops)
    v = {(r, c): (b, a) for op in ops if op["cell"] == [0, 0] for r, c, b, a in op["verts"]}
    assert v[(2, 2)] == (10.0, 50.0)                 # the centre: before the row's 10, after 10 + 40
    assert all(a - b < 40 for (r, c), (b, a) in v.items() if (r, c) != (2, 2))   # eased away from the centre


def test_land_refuses_past_the_bound_or_outside_the_footprint():
    files = {"place": PLACE, "land": [{"cell": [0, 0], "verts": [[2, 2, 90.0]]}]}
    with pytest.raises(ValueError, match="land bound"):
        land_ops(files, None, ["256,256", "300", "40"], {"why": "x"})
    with pytest.raises(ValueError, match="footprint"):
        land_ops({"place": PLACE, "land": []}, None, ["8300,0", "300", "40"], {"why": "x"})
