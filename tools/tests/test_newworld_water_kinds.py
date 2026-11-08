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
