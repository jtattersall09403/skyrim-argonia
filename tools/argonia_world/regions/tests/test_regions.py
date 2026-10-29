"""L1/L2 on small fixtures: the migration's rows, the classifier's helpers, the region record writers' maths."""
from tools.argonia_world import skyrim_units as su
from tools.argonia_world.regions import api
from tools.argonia_world.regions import classify as K
from tools.argonia_world.regions import migrate as M


def _docs():
    states = [{"id": s, "name": s.title(), "visibilityFactor": 1.0, "wetness": 0.0}
              for s in ("clear-humid", "ground-mist", "storm")]
    weather = {"states": states, "regionFrequencies": {k: {"clear-humid": 5, "storm": 1} for k in M.GROUPS},
               "seasons": [{"id": "wet", "name": "Wet", "share": 0.5, "effects": "rain"},
                           {"id": "dry", "name": "Dry", "share": 0.5, "effects": "sun"}]}
    pal = {"byRegionClass": {str(rid): {"note": None, "layers": [
        {"role": next(iter(M.ROLE_OF)), "instances_per_hectare": 4, "clump_size_median": 2, "clump_radius_m": 3}]}
        for rid, _, _, _ in M.RASTER}}
    over = {"confidence": "owner", "overrides": [{"id": "o1", "regionClass": M.RASTER[0][0],
                                                  "polygonUV": [[0, 0], [1, 0], [1, 1]],
                                                  "appliesToClasses": [M.RASTER[1][0]]}]}
    return weather, over, pal


def test_rows_from_keys_every_table():
    out = M.rows_from(*_docs())
    assert len(out["weather_state"]) == 3
    assert len(out["weather_group_weight"]) == 2 * len(M.GROUPS)
    assert [p["ord"] for p in out["region_class_override_point"]] == [0, 1, 2]
    assert len(out["region_class_profile"]) == len(M.RASTER)
    assert {r["season_id"] for r in out["season"] and out["season_factor"]} <= {"wet", "dry", "hatching"}


def test_runs_tile_each_row():
    grid = [["a", "a", "b"], ["c", "c", "c"]]
    rs = K.runs(grid)
    assert [(r["cx1"] - r["cx0"] + 1, r["land_region_id"]) for r in rs] == [(2, "a"), (1, "b"), (3, "c")]
    assert rs[0]["cy"] != rs[2]["cy"]


def test_majority_removes_speckle_only():
    g = [["a"] * 3, ["a", "b", "a"], ["a"] * 3]
    assert K.majority(g)[1][1] == "a"
    g = [["a", "b", "b"], ["a", "b", "a"], ["a"] * 3]
    assert K.majority(g)[1][1] == "b"  # it has a neighbour of its own class


def test_in_polygon():
    sq = [(0, 0), (1, 0), (1, 1), (0, 1)]
    assert K.in_polygon(0.5, 0.5, sq) and not K.in_polygon(1.5, 0.5, sq)


def test_vote_is_deterministic():
    assert K.vote(["b", "a", "b", "a"]) == "a"


def test_rectangles_merge_rows_and_cover_every_cell():
    runs = [{"cy": 0, "cx0": 0, "cx1": 2}, {"cy": 1, "cx0": 0, "cx1": 2}, {"cy": 2, "cx0": 1, "cx1": 1},
            {"cy": 4, "cx0": 0, "cx1": 2}]
    rects = api.rectangles(runs)
    assert rects == [(0, 0, 2, 1), (1, 2, 1, 2), (0, 4, 2, 4)]
    cells = {(x, y) for x0, y0, x1, y1 in rects for x in range(x0, x1 + 1) for y in range(y0, y1 + 1)}
    assert len(cells) == 3 + 3 + 1 + 3


def test_area_is_the_cells_outline_in_units():
    pts = api.area(-1, 2, 0, 2)
    assert pts[0] == [-su.CELL_UNITS, 2 * su.CELL_UNITS] and pts[2] == [su.CELL_UNITS, 3 * su.CELL_UNITS]


def test_weather_colours_stay_in_bytes_and_night_is_darker():
    images = {i: {"tint": t} for i, t in (("d", "C8BC6A"), ("a", "D8A458"), ("n", "5A7A4E"))}
    col = api.weather_colours("8C9A6E", images, {"image_day_id": "d", "image_dawn_id": "a", "image_night_id": "n"})
    assert set(api.LADDER) <= set(col)
    for slot in col.values():
        for c in slot.values():
            assert all(0 <= v <= 255 for v in c)
    assert sum(col["skyUpper"]["night"]) < sum(col["skyUpper"]["day"])
    amb = api.ambient(col)
    assert amb["day"]["zPlus"] == col["ambient"]["day"] and sum(amb["day"]["zMinus"]) < sum(amb["day"]["zPlus"])


def test_object_list_mixes_classes_by_share(monkeypatch):
    class W:
        def query(self, sql, *a):
            if "object_form" in sql:
                return [{"form_key": "000001:Skyrim.esm", "role_id": "rock"},
                        {"form_key": "000002:Skyrim.esm", "role_id": "rock"}]
            return [{"role_id": "rock", "per_ha": 4.0 if a[0] == "x" else 0.0, "clump_median": 2,
                     "clump_radius_m": 5, "slope_max_deg": 30, "water_min_m": None, "water_max_m": None}]
    out = K.object_list(W(), {"x": 1, "y": 1})
    assert [o["density_per_ha"] for o in out] == [1.0, 1.0]  # 4/ha over half the cells, split over two forms
    assert all(o["conform"] for o in out)
