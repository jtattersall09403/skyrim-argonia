from tools.newworld import water_kinds as wk
from tools.newworld import water_overrides_pull as pull


def test_region_wet_character_reads_the_research():
    ch = wk.region_character()
    assert ch["murkwood"]["wet"] == "blackwater-swamp"      # Hist swamp forest
    assert ch["ultherus-swamp"]["wet"] == "green-marsh"     # cattail and reed swamp
    assert ch["chixathe-mesa"]["wet"] == "pond"             # dry mesa


def test_pull_turns_editor_documents_into_overrides_and_strokes():
    edits = {"wb-1-2": {"kind": "river", "flows": True, "flow_deg": 370, "speed": "fast", "name": "Test", "by": "x"},
             "wb-3-4": {"kind": "lava"}}
    paint = {"b": {"kind": "green-marsh", "flows": False, "radius_px": 30, "pts": [1, 2, 3, 4], "at": "2"},
             "a": {"kind": "pond", "pts": [5, 6], "at": "1"}}
    ov, strokes, problems = pull.convert(edits, paint)
    assert ov == {"wb-1-2": {"water_kind_id": "river", "flows": True, "flow_toward_deg": 10, "speed": "fast",
                             "name": "Test"}}
    assert [s["id"] for s in strokes] == ["a", "b"] and strokes[1]["points"] == [[1, 2], [3, 4]]
    assert problems == ["wb-3-4: unknown kind lava"]


def test_flow_runs_down_the_channel_graph_into_the_main_channel_and_the_sea():
    import numpy as np
    r = np.zeros((60, 80), np.int32)
    r[:, :10] = 1                      # sea on the west
    r[30:34, 10:70] = 2                # main channel, east to west
    r[5:30, 50:53] = 3                 # tributary from the north joining it
    kind_of = np.array(["land", "ocean", "river", "stream"])
    g, outlet = wk.outlet_distance(r, kind_of)
    vec = wk.flow_vectors(wk.descent(g, r > 0), r.shape, 3)
    assert vec[1][31, 40] < 0 and abs(vec[0][31, 40]) <= 2      # main channel runs west, along itself
    assert vec[0][10, 51] > 0                                   # tributary runs south into the junction
    assert not np.isfinite(g[r == 1]).any()                     # the sea itself does not flow


def _row(i, kind, area, set_by="derived"):
    return {"raster_index": i, "id": f"b{i}", "kind": kind, "area_m2": area, "set_by": set_by, "why": "",
            "region_id": None, "open_m": 10.0}


def test_a_fringe_of_little_channels_takes_its_marsh_kind_and_a_real_channel_stays():
    import numpy as np
    r = np.zeros((40, 60), np.int32)
    r[10:30, 10:30] = 1                # an owner's swamp
    r[18:20, 30:36] = 2                # a stub on its edge: only the swamp touches it
    r[22:24, 30:50] = 3                # a channel from the swamp to the sea
    r[:, 50:] = 4
    rows = [_row(1, "blackwater-swamp", 4e5, "owner"), _row(2, "stream", 100), _row(3, "stream", 300),
            _row(4, "ocean", 1e7)]
    assert wk.absorb_fringes(r, rows) == 1
    assert rows[1]["kind"] == "blackwater-swamp" and rows[2]["kind"] == "stream"


def test_a_channel_with_no_water_surface_to_the_sea_is_still_and_the_map_edge_is_no_outlet():
    import numpy as np
    r = np.zeros((40, 60), np.int32)
    r[0:12, 20:23] = 1                 # a stream cut by the map's top edge, nowhere near the sea
    r[25:28, 0:50] = 2                 # a stream to the sea
    r[:, 50:] = 3
    rows = [_row(1, "stream", 500), _row(2, "stream", 900), _row(3, "ocean", 1e7)]
    assert wk.no_sea_still(r, rows, {}) == 1
    assert rows[0]["kind"] not in wk.RUNNING and rows[1]["kind"] == "stream"
    g, outlet = wk.outlet_distance(r, np.array(["land", "stream", "stream", "ocean"]))
    assert not (outlet == 2).any()


def test_an_old_edit_without_a_point_is_found_by_the_point_its_id_names():
    import numpy as np
    r = np.zeros((20, 20), np.int32)
    r[5:10, 5:10] = 1
    ov, lost = wk.resolve_overrides({"wb-7-6": {"water_kind_id": "pond"}}, [_row(1, "stream", 50)], r)
    assert ov == {"b1": {"water_kind_id": "pond"}} and lost == []


def test_arrows_follow_the_channel_round_its_bend_toward_the_sea():
    import numpy as np
    r = np.zeros((60, 60), np.int32)
    r[5:9, 5:40] = 1                   # east along the top, then south down to the sea
    r[5:50, 36:40] = 1
    r[50:, :] = 2
    kind_of = np.array(["land", "stream", "ocean"])
    g, _ = wk.outlet_distance(r, kind_of)
    vec = wk.flow_vectors(wk.descent(g, r > 0), r.shape, 3)
    rows = [{"raster_index": 1, "kind": "stream"}, {"raster_index": 2, "kind": "ocean"}]
    arrows = wk.arrow_samples(r, rows, vec, g, step=30, steps=60)
    bent = [a for a in arrows if a[4] < 30 and a[5] < 10]
    assert bent
    xs, ys = bent[0][4::2], bent[0][5::2]
    assert max(xs) > xs[0] and ys[-1] > ys[0]                   # it runs east, then turns south along the bend
