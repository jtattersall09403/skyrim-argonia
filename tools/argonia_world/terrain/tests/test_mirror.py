"""L1: positions keep the province's north at Skyrim's +y (the 2.W1 finding: imported y runs south)."""
from tools.argonia_world import skyrim_units as su
from tools.argonia_world.intermediate import _pos_exterior, _pos_interior


def test_exterior_north_is_up_and_on_the_grid():
    side_m = (su.PROVINCE_SAMPLES - 1) * su.PROVINCE_SAMPLE_M
    nw, se = _pos_exterior([0.0, 0.0, 0.0]), _pos_exterior([side_m, side_m, 10.0])
    x0, y0 = su.PROVINCE_CELL_SW
    top = (y0 + su.PROVINCE_CELLS) * su.CELL_UNITS
    assert nw[:2] == [x0 * su.CELL_UNITS, top] and se[:2] == [(x0 + su.PROVINCE_CELLS) * su.CELL_UNITS, y0 * su.CELL_UNITS]
    assert se[2] == su.rounded(su.metres_to_units(10.0), 2)
    # a sample's position lands on its LAND vertex: row r from the north is cell-local vertex row 32 - r % 32
    r, c = 70, 37
    x, y, _ = _pos_exterior([c * su.PROVINCE_SAMPLE_M, r * su.PROVINCE_SAMPLE_M, 0.0])
    assert (x - x0 * su.CELL_UNITS) / su.VERTEX_SPACING_UNITS == c and (top - y) / su.VERTEX_SPACING_UNITS == r


def test_interior_y_south_becomes_minus_y():
    assert _pos_interior([1.0, 2.0, 3.0]) == [su.rounded(su.metres_to_units(1.0), 2),
                                             su.rounded(-su.metres_to_units(2.0), 2), su.rounded(su.metres_to_units(3.0), 2)]
    assert _pos_interior([0.0, 0.0, 0.0]) == [0.0, 0.0, 0.0]
