"""The new world's LOD settings and expected terrain LOD files (tools/newworld/world/mapdata.py)."""
import struct

from tools.newworld.world import mapdata
from tools.newworld.world import units as su


def grid(cx0, cy_top, nx, ny):
    return su.Grid("t", nx * 32 + 1, ny * 32 + 1, cx0 * 4096.0, (cy_top + 1) * 4096.0, 0.0)


def test_lod_settings_follow_valenwoods_rule():
    # the SW corner on the level-32 grid, the stride the power of two over the span (Valenwood: -32,-32,128,4,32)
    g = grid(-84, -95, 182, 148)  # the current build's grid
    x0, y0, stride, lo, hi = mapdata.lod_settings(g)
    assert (x0, y0, lo, hi) == (-96, -256, 4, 32)
    assert x0 % 32 == 0 and y0 % 32 == 0 and stride == 256
    assert len(struct.pack("<hhiii", x0, y0, stride, lo, hi)) == 16


def test_expected_covers_every_cell_once_per_level():
    g = grid(-3, 4, 10, 6)  # cells x -3..6, y -1..4
    exp = mapdata.expected(g)
    for lvl, files in exp.items():
        btr = [f for f in files if f.endswith(".btr")]
        assert len(files) == 3 * len(btr)
        covered = set()
        for f in btr:
            _, L, x, y, _ = f.rsplit("\\", 1)[1].split(".")
            assert int(L) == lvl and int(x) % lvl == 0 and int(y) % lvl == 0
            covered |= {(cx, cy) for cx in range(int(x), int(x) + lvl) for cy in range(int(y), int(y) + lvl)}
        assert {(cx, cy) for cx in range(-3, 7) for cy in range(-1, 5)} <= covered


def scope(tmp_path, cells, margin):
    import json
    (tmp_path / "scope_cells.json").write_text(json.dumps(cells))
    (tmp_path / "margin_cells.json").write_text(json.dumps(margin))
    return tmp_path


def test_map_box_spans_the_whole_province_inside_the_built_cells(tmp_path):
    # the walk-5 fault: the box sat a quarter in from each side, so the far west, south and east could not be reached
    g = grid(-84, -95, 182, 148)  # x -84..97, y -242..-95
    prov = [[mx, my] for mx in range(-38, 44) for my in range(-116, -51)]  # Skyrim cells x -76..87, y -232..-103
    margin = [[-42, -60], [47, -100]]
    box = mapdata.map_box(g, scope(tmp_path, prov + margin, margin))
    assert box["nw"] == [-76, -103] and box["se"] == [87, -232]
    # a province wider than the built cells is held MAP_MARGIN inside them
    wide = [[mx, my] for mx in range(-45, 50) for my in range(-125, -45)]
    box = mapdata.map_box(g, scope(tmp_path, wide, []))
    assert box["nw"] == [-84 + mapdata.MAP_MARGIN, -95 - mapdata.MAP_MARGIN]
    assert box["se"] == [97 - mapdata.MAP_MARGIN, -242 + mapdata.MAP_MARGIN]


def test_camera_height_follows_the_box_from_tamriels():
    assert mapdata.camera({"nw": [-30, 15], "se": [40, -40]})["max_height"] == 80000  # Tamriel's own box
    assert mapdata.camera({"nw": [-76, -103], "se": [87, -232]})["max_height"] == 160000  # at most twice
    assert mapdata.camera({"nw": [0, 10], "se": [10, 0]})["max_height"] == 80000  # never below Tamriel's
