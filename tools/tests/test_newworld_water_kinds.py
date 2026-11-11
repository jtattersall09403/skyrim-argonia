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


def test_the_map_kind_is_read_not_the_owners_kind_the_terrain_laid_over_it():
    import numpy as np
    bj = [{"raster_index": 1, "water_kind_id": "lake", "why": "owner override", "overridden": True,
           "map_kind": "stream", "map_why": "a channel under ~23 m wide"},
          {"raster_index": 2, "water_kind_id": "river", "why": "a channel over ~23 m wide", "overridden": None,
           "map_kind": "river", "map_why": "a channel over ~23 m wide"}]
    assert wk.map_kinds(bj, np.zeros((4, 4), np.int32)) == {1: ("stream", "a channel under ~23 m wide"),
                                                           2: ("river", "a channel over ~23 m wide")}
    plain = [{"raster_index": 1, "water_kind_id": "pond", "why": "w", "overridden": None}]   # no edits laid over
    assert wk.map_kinds(plain, np.zeros((4, 4), np.int32)) == {1: ("pond", "w")}


def test_a_lake_the_map_edge_cuts_is_a_lake_and_edge_water_joined_to_a_sea_region_is_sea():
    import numpy as np
    from tools.newworld import terrain_water as tw
    water = np.zeros((220, 420), bool)
    water[0:90, 40:130] = True          # a lake in the neighbour's land, cut by the map's north edge
    water[100:220, 250:420] = True      # open water reaching the east edge and a sea region
    code = np.full(water.shape, -1, np.int32)
    code[150:, 300:] = 0
    raster, bodies = tw.label_bodies(water, code, ["the-sea"], {"the-sea": "sea"}, {}, 2.93)

    def kind_at(y, x):
        return next(b["water_kind_id"] for b in bodies if b["raster_index"] == raster[y, x])
    assert kind_at(40, 80) in ("lake", "pond")
    assert kind_at(180, 380) == "ocean" and kind_at(110, 270) == "ocean"


def _held_case():
    """A river (body 1, 4000 px) with a small bit beside it (body 2, 60 px) that the owner called a lake."""
    import numpy as np
    r = np.zeros((120, 200), np.int32)
    r[40:60, 0:200] = 1
    r[60:66, 100:110] = 2
    rows = [{"raster_index": 1, "id": "wb-100-50", "water_kind_id": "river", "area_m2": 4000 * 8.56},
            {"raster_index": 2, "id": "wb-104-62", "water_kind_id": "lake", "area_m2": 60 * 8.56}]
    ov = {"wb-100-50": {"at": "1", "point": [100, 50], "water_kind_id": "river", "flows": True},
          "wb-104-62": {"at": "2", "point": [104, 62], "water_kind_id": "lake", "flows": False},
          "wb-20-50": {"at": "3", "point": [20, 50], "name": "A name"}}
    return r, rows, ov


def test_an_edit_records_the_water_it_was_made_on_and_is_checked_against_it():
    import numpy as np
    from tools.newworld import water_held as wh
    r, rows, ov = _held_case()
    held = np.zeros(r.shape, np.int32)
    assert wh.record(ov, held, r, rows) == []
    assert ov["wb-104-62"]["area_m2"] == 60 * 8.56 and ov["wb-100-50"]["held"] != ov["wb-104-62"]["held"]
    assert "held" not in ov["wb-20-50"] and ov["wb-20-50"]["area_m2"] == 4000 * 8.56   # a name: found by its point
    assert (held == ov["wb-104-62"]["held"]).sum() == 60 and wh.kinds(ov)[ov["wb-104-62"]["held"]] == "lake"
    assert wh.check(ov, r, rows) == {"edits": 3, "same": 3, "overtaken": 0, "no_record": [], "off": [], "lost": []}
    # the fault of 2026-11-11: a rebuild joins the bit to its river, and the lake edit, the later, takes the river
    joined = np.where(r > 0, 1, 0).astype(np.int32)
    one = [{"raster_index": 1, "id": "wb-100-50", "water_kind_id": "lake", "area_m2": 4060 * 8.56}]
    res = wh.check(ov, joined, one)
    assert [o["edit"] for o in res["off"]] == ["wb-100-50", "wb-104-62"] and res["off"][0]["wanted"] == "river"
    # a second record keeps what is recorded; an edit made later on held water shares its index
    ov["wb-110-64"] = {"at": "4", "point": [108, 64], "water_kind_id": "pond"}
    wh.record(ov, held, r, rows)
    assert ov["wb-110-64"]["held"] == ov["wb-104-62"]["held"] and wh.kinds(ov)[ov["wb-110-64"]["held"]] == "pond"
    rows[1]["water_kind_id"] = "pond"
    assert wh.check(ov, r, rows)["overtaken"] == 1          # the lake edit, overtaken by the pond edit on its water


def test_the_kinds_check_fails_on_a_kind_that_moved_unless_the_waterline_did(tmp_path, monkeypatch):
    import json
    import numpy as np
    from tools.newworld import frame as f
    monkeypatch.setattr(f, "OUT", tmp_path)
    monkeypatch.setattr(wk, "ACCEPTED", tmp_path / "water_accepted.json")
    r = np.zeros((400, 600), np.int32)
    r[100:150, 100:500] = 1             # a river
    r[200:300, 100:300] = 2             # a marsh
    rows = [{"raster_index": 1, "id": "a", "water_kind_id": "river", "area_m2": 1.0, "label_px": 300, "label_py": 125},
            {"raster_index": 2, "id": "b", "water_kind_id": "green-marsh", "area_m2": 1.0, "label_px": 200, "label_py": 250}]
    first = wk.checks(r, rows, {})      # nothing accepted yet: this classification becomes the record
    assert first["ok"] and json.loads(wk.ACCEPTED.read_text())["kinds"]["river"]["bodies"] == 1
    rows[0]["water_kind_id"] = "lake"   # the river turned lake on the same waterline
    res = wk.checks(r, rows, {})
    assert not res["ok"] and not res["waterline_moved"] and {o["kind"] for o in res["kinds_off"]} == {"river", "lake"}
    r[160:190, 100:500] = 1             # the waterline itself moved: nothing to compare, looked at afresh
    assert wk.checks(r, rows, {})["waterline_moved"]
    assert wk.checks(r, rows, {}, accept=True)["ok"] and not wk.checks(r, rows, {})["kinds_off"]


def test_a_pulled_edit_made_at_another_point_drops_the_water_recorded_for_it():
    had = {"wb-1-2": {"point": [1, 2], "water_kind_id": "pond", "area_m2": 50.0, "held": 3},
           "wb-5-6": {"point": [5, 6], "water_kind_id": "lake", "area_m2": 70.0, "held": 4}}
    out = pull.merge(had, {"wb-1-2": {"point": [9, 9], "water_kind_id": "lake"},
                           "wb-5-6": {"point": [5, 6], "water_kind_id": "river"}})
    assert out["wb-1-2"] == {"point": [9, 9], "water_kind_id": "lake"}
    assert out["wb-5-6"] == {"point": [5, 6], "water_kind_id": "river", "area_m2": 70.0, "held": 4}


def test_verify_reads_the_water_check_as_two_rows(tmp_path):
    import json
    from tools.newworld import water_held as wh

    class Rep:
        def __init__(self):
            self.rows = []

        def row(self, area, req, value, ok, detail=""):
            self.rows.append((req, bool(ok), detail))

        def fail(self, area, req, missing):
            self.row(area, req, "-", False, missing)

    rep = Rep()
    wh.rows(rep, tmp_path / "water_check.json")
    assert [ok for _, ok, _ in rep.rows] == [False]                 # no check written: a failed row, not silence
    check = {"accepted_build": "a", "terrain_build": "b", "waterline_moved": False,
             "kinds_off": [{"kind": "river", "bodies": 21, "accepted_bodies": 24, "area_m2": 1012180,
                            "accepted_area_m2": 2080478}],
             "edits": {"edits": 289, "same": 259, "overtaken": 12, "no_record": [], "lost": [],
                       "off": [{"edit": "wb-1807-1384", "body": "wb-1300-1162", "area_m2": 1050664.6,
                                "recorded_m2": 487.9, "kind": "lake"}]}}
    (tmp_path / "water_check.json").write_text(json.dumps(check))
    rep = Rep()
    wh.rows(rep, tmp_path / "water_check.json")
    assert [ok for _, ok, _ in rep.rows] == [False, False] and "river: 21 bodies 101.2 ha" in rep.rows[0][2]
    check["kinds_off"], check["edits"]["off"] = [], []
    (tmp_path / "water_check.json").write_text(json.dumps(check))
    rep = Rep()
    wh.rows(rep, tmp_path / "water_check.json")
    assert [ok for _, ok, _ in rep.rows] == [True, True]


def test_the_owners_held_water_takes_its_kind_in_the_terrains_bodies_never_by_id():
    import numpy as np
    from tools.newworld import terrain_water as tw
    raster = np.zeros((60, 120), np.int32)
    raster[20:30, 0:120] = 1                      # a river
    raster[40:50, 10:30] = 2                      # a pond
    bodies = [{"id": "wb-0-24", "raster_index": 1, "water_kind_id": "river", "area_m2": 1200 * 8.56, "label_px": 0,
               "label_py": 24, "region_id": None, "why": "a channel", "map_kind": "river", "map_why": "a channel"},
              {"id": "wb-19-44", "raster_index": 2, "water_kind_id": "pond", "area_m2": 200 * 8.56, "label_px": 19,
               "label_py": 44, "region_id": None, "why": "still", "map_kind": "pond", "map_why": "still"}]
    held = np.zeros(raster.shape, np.int32)
    held[20:30, 80:120] = 1                       # the owner's lake: the river's east end
    held[40:50, 10:30] = 2                        # the owner's marsh: the whole pond
    held[0:5, 0:5] = 3                            # held water the map no longer has
    held[20:30, 0:10] = 4                         # the owner's river on the river: nothing to change
    lost = tw.hold(raster, bodies, held, {1: "lake", 2: "green-marsh", 3: "pond", 4: "river"})
    assert lost == ["held water 3 (pond) lies on no water"]
    assert len(bodies) == 3 and (raster == 3).sum() == 400 and (raster == 1).sum() == 800
    river, pond, lake = bodies
    assert (river["water_kind_id"], pond["water_kind_id"], lake["water_kind_id"]) == ("river", "green-marsh", "lake")
    assert lake["map_kind"] == "river" and lake["overridden"] and lake["area_m2"] == round(400 * 8.56, 1)
    assert raster[lake["label_py"], lake["label_px"]] == 3 and raster[river["label_py"], river["label_px"]] == 1
    assert river["area_m2"] == round(800 * 8.56, 1) and lake["id"] != river["id"]
