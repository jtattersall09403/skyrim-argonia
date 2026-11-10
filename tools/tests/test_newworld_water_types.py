"""The new world's water types (world/water_types.py), the land against the water plane (quantize.off_plane) and
the water read-back rows (world/water_check.py)."""
import json

import numpy as np

from tools.newworld import verify as v
from tools.newworld.world import quantize, water_check as wc, water_types as wt


def test_running_water_keys_by_heading_and_still_water_by_kind():
    assert wt.key_for("river", 50, "pond") == "river-045"
    assert wt.key_for("stream", 349, "pond") == "stream-000"       # 349 snaps to north, not 360
    assert wt.key_for("river", None, "blackwater-swamp") == "blackwater-swamp"   # a channel that does not flow here
    assert wt.key_for("estuary", 170, "pond") == "estuary-180"
    assert wt.key_for("estuary", None, "pond") == "estuary"
    assert wt.key_for("lake", None, "pond") == "pond" and wt.key_for("ocean", None, "pond") == "sea"


def test_specs_carry_heading_speed_and_still_types_no_current():
    r = wt.spec("river-135")
    assert r["edid"] == "ANW_RiverWaterFlow_135" and r["heading"] == 135 and r["speed"] > 0
    assert v.FLOW.search(r["edid"]) and v.FLOW.search(wt.spec("stream-000")["edid"])
    for k in ("sea", "pond", "green-marsh", "blackwater-swamp", "estuary"):
        s = wt.spec(k)
        assert "heading" not in s and s["set"]["LinearVelocity"] == [0, 0, 0], k
        assert not v.FLOW.search(s["edid"]), k   # a still type is never named as flowing water
    recs = wt.records(["river-045", "pond"])
    assert set(recs) == {"river-045", "pond", "sea"}


def test_kinds_differ_in_look():
    def vec(k):
        s = wt.KINDS[k]["set"]
        return s["ShallowColor"] + s["DeepColor"] + s["ReflectionColor"] + [s["Opacity"]]
    ks = list(wt.KINDS)
    near = min(max(abs(a - b) for a, b in zip(vec(p), vec(q))) for i, p in enumerate(ks) for q in ks[i + 1:])
    assert near >= 25


def test_off_plane_moves_rounded_vertices_to_their_own_side():
    h = np.array([[3.0, -3.0, 0.0, 9.0, -20.0]])
    steps = np.rint(h / 8).astype(np.int64)
    assert quantize.off_plane(steps, h, 0.0, 8.0) == 3
    assert steps.tolist() == [[1, -1, 1, 1, -2]]
    assert quantize.off_plane(steps, h, 4.0, 8.0) == 0      # a level between steps: nothing can sit on it


def _cell(steps: np.ndarray) -> bytes:
    off, d = quantize.encode(steps)
    return np.float32(off).tobytes() + d.tobytes() + bytes(33 * 33 * 3)


def test_heights_decode_and_shore_counts(tmp_path):
    yy, xx = np.mgrid[0:33, 0:33]
    a = (xx - 16).astype(np.int64)                 # a slope crossing the plane at x = 16: one vertex column on it
    b = np.where(xx < 16, -2, 3).astype(np.int64)  # a bank: off the plane on both sides
    assert np.array_equal(wc.heights(_cell(a)), a * 8.0)
    land = tmp_path / "land"
    land.mkdir()
    (land / "cy+000.bin").write_bytes(_cell(a) + _cell(b))
    (land / "manifest.json").write_text(json.dumps({"grid": {"water": 0.0, "cells_x": 2}, "cell_bytes": 4 + 33 * 33 * 4,
                                                   "shards": ["cy+000.bin"]}))
    s = wc.shore(tmp_path)
    assert s["on_plane"] == 33 and s["within_fight_band"] == 33
    assert s["crossing_edges"] == 33 + 33       # the slope's edge onto the plane rises 8, the bank's 40
    assert s["rise_p10_median_p90"][0] == 8.0 and s["rise_p10_median_p90"][2] == 40.0


def test_rows_fail_on_one_look_and_pass_on_distinct_kinds():
    shore = {"vertices_near": 10, "within_fight_band": 0, "on_plane": 0, "crossing_edges": 4, "rise_p10_median_p90": [24, 40, 96]}
    same = {"kinds": {"sea": {"cells": 10, "pure": 0, "pure_share": 0.0, "mean_look": [1] * 10},
                      "river": {"cells": 5, "pure": 0, "pure_share": 0.0, "mean_look": [1] * 10}},
            "pairs": [["river", "sea", 3.0]], "flowing_cells": 5, "velocity_within_22_5": 2, "noise_within_22_5": 1,
            "velocity_err_p50_p90_max": [30, 80, 170], "noise_err_p50_p90_max": [30, 80, 170], "flow_examples_off": [],
            "still_cells": 10, "still_cells_with_flow": 10, "edge_steps": 3, "edge_step_p50_p99_max": [1, 2, 3]}
    rep = v.Report()
    wc.rows(rep, same, shore)
    res = {r["requirement"].split(":")[0].split(" (")[0]: r["result"] for r in rep.rows}
    assert res["sea"] == "FAIL" and res["river"] == "FAIL"
    assert res["flowing cells run with the channel graph"] == "FAIL"
    assert res["still kinds"] == "FAIL"
    good = dict(same, pairs=[["river", "sea", 60.0]], velocity_within_22_5=5, noise_within_22_5=5, still_cells_with_flow=0,
                kinds={"sea": dict(same["kinds"]["sea"], pure_share=0.8), "river": same["kinds"]["river"]})
    rep = v.Report()
    wc.rows(rep, good, shore)
    assert all(r["result"] == "PASS" for r in rep.rows), [r for r in rep.rows if r["result"] != "PASS"]
