"""The frame of the new world holds when the terrain grid grows: a place keeps its game coordinates and its Skyrim
cell, a map pixel keeps its ground, and the owner's water edits stay on their water. The two grids are the build
before the world was widened (5825 x 4737 samples) and the one after (6849 x 5761: 8 map cells more on every side,
so the old grid sits at sample (512, 512) of the new)."""
import json

import numpy as np
from PIL import Image

from tools.newworld import frame as f
from tools.newworld import landcover
from tools.newworld import terrain
from tools.newworld import water_held as wh
from tools.newworld import water_kinds as wk
from tools.newworld.world import units as su

OLD = su.Grid("old", 5825, 4737, -344064.0, -385024.0, 0.0)
NEW = su.Grid("new", 6849, 5761, -409600.0, -319488.0, 0.0)
DB = f.ROOT / "story" / "data" / "db"
PLACES = {p["id"]: p for p in map(json.loads, (DB / "place.jsonl").read_text().splitlines())}


def sample(g: su.Grid, x: float, y: float) -> tuple[int, int]:
    return round((g.origin_y - y) / su.VERTEX_SPACING_UNITS), round((x - g.origin_x) / su.VERTEX_SPACING_UNITS)


def test_a_place_keeps_its_game_coordinates_and_cell_when_the_grid_grows():
    for pid, cell in (("helstrom", (-8, -148)), ("stormhold", (-4, -124))):
        p = PLACES[pid]
        assert (int(p["world_x"] // su.CELL_UNITS), int(p["world_y"] // su.CELL_UNITS)) == cell
        (ro, co), (rn, cn) = sample(OLD, p["world_x"], p["world_y"]), sample(NEW, p["world_x"], p["world_y"])
        assert (rn - ro, cn - co) == (512, 512)                      # the grid grew at the origin corner
        for g, (r, c) in ((OLD, (ro, co)), (NEW, (rn, cn))):         # the cell's own samples hold the place in both
            r0, r1 = g.cell_rows(cell[1])
            c0, c1 = g.cell_cols(cell[0])
            assert r0 <= r <= r1 and c0 <= c <= c1
            # and a sample's game coordinates come from the grid's own origin
            assert abs(g.origin_x + c * su.VERTEX_SPACING_UNITS - p["world_x"]) <= 64
            assert abs(g.origin_y - r * su.VERTEX_SPACING_UNITS - p["world_y"]) <= 64
    assert (OLD.cx0, OLD.cy_top) == (-84, -95) and (NEW.cx0, NEW.cy_top) == (-100, -79)


def test_the_map_pixel_of_a_place_is_the_same_from_either_grid():
    p = PLACES["helstrom"]
    for g in (OLD, NEW):
        r, c = sample(g, p["world_x"], p["world_y"])
        py, px = landcover.sample_to_px(r, c, g.origin_x, g.origin_y)
        assert abs(px - p["px"]) < 1 and abs(py - p["py"]) < 1
    x, y = f.px_to_world(p["px"], p["py"])
    assert abs(x - p["world_x"]) < 1 and abs(y - p["world_y"]) < 1


def test_the_regions_raster_is_in_map_pixels_whatever_the_grid():
    p = PLACES["helstrom"]
    cell = f.px_to_cell(p["px"], p["py"])
    rp = terrain.region_px({f"{cell[0]},{cell[1]}": "murkwood", f"{cell[0] - 60},{cell[1]}": "past the picture"},
                           ["murkwood", "past the picture"], (f.HEIGHT_PX, f.WIDTH_PX))
    assert rp.shape == (f.HEIGHT_PX, f.WIDTH_PX) and rp[int(p["py"]), int(p["px"])] == 0
    assert (rp == 0).sum() == f.PX_PER_CELL ** 2 and not (rp == 1).any()    # a cell past the picture has no pixels


def test_a_map_pixel_reads_its_ground_through_the_builds_origin(tmp_path, monkeypatch):
    """water_kinds.heights_px (the atlas's terrain layer uses the same conversion): the same ground under a map
    pixel from a small grid and from one grown by 16 samples at the origin corner."""
    monkeypatch.setattr(f, "OUT", tmp_path)
    (tmp_path / "terrain").mkdir()
    shape = (40, 60)                                               # map px, the picture's north-west corner
    x0, y0 = f.px_to_world(0, 0)

    def write(pad: int):
        ox, oy = x0 - pad * 128.0, y0 + pad * 128.0
        rows, cols = 80 + 2 * pad, 120 + 2 * pad
        rr, cc = np.mgrid[0:rows, 0:cols]
        h = ((ox + cc * 128.0) * 0.01 + (oy - rr * 128.0) * 0.02).astype(np.float32) * f.UNITS_PER_METRE
        np.save(tmp_path / "terrain" / "heightmap.npy", h)
        (tmp_path / "terrain" / "build.json").write_text(json.dumps(
            {"origin_world_x": ox, "origin_world_y": oy, "sample_units": 128.0}))
        return wk.heights_px(shape)

    small, grown = write(0), write(16)
    assert np.allclose(small, grown, atol=1e-2)
    wx, wy = f.px_to_world(20.5, 12.5)
    assert abs(small[12, 20] - (wx * 0.01 + wy * 0.02)) < 3.0      # within a sample of the ground at that pixel


def test_the_owners_water_edits_and_their_held_water_share_the_maps_frame():
    """Every edit carries the area of the body it was made on; every kind edit's point lies on its held water; the
    held raster is the map's size (a raster in another frame is refused)."""
    ov = json.loads(wh.OVERRIDES.read_text())
    held = wh.load((f.HEIGHT_PX, f.WIDTH_PX))
    assert np.asarray(Image.open(wh.PNG)).shape == (f.HEIGHT_PX, f.WIDTH_PX)
    kinds = wh.kinds(ov)
    for key, o in ov.items():
        assert o.get("area_m2") is not None, key
        if o.get("water_kind_id"):
            assert o["held"] in kinds and wh.body_at(held, *wh.point_of(key, o)) == o["held"], key
    try:
        wh.load((f.HEIGHT_PX + 1024, f.WIDTH_PX + 1024))
    except ValueError:
        pass
    else:
        raise AssertionError("a held raster of another size was accepted")
