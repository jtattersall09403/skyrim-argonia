"""The new world's water types (world/water_types.py), their records and seams (ArgoniaPlugin WaterBlend.cs, through
`waterstudy selftest` and `waterstudy plan`), the land against the water plane (quantize.off_plane) and the water
read-back rows (world/water_check.py)."""
import json
import os
import subprocess
from pathlib import Path

import numpy as np
import pytest

from tools.newworld import verify as v
from tools.newworld.world import quantize, water_check as wc, water_types as wt

REPO = Path(__file__).resolve().parents[2]
DOTNET = Path.home() / ".dotnet"
DATA = Path(os.environ.get("ARGONIA_GAME_ROOT", Path.home() / "games/skyrimse")) / "Data"


def test_running_water_keys_by_heading_and_still_water_by_kind():
    assert wt.key_for("river", 50, "pond") == "river-045"
    assert wt.key_for("stream", 349, "pond") == "stream-000"       # 349 snaps to north, not 360
    assert wt.key_for("river", None, "blackwater-swamp") == "blackwater-swamp"   # a channel that does not flow here
    assert wt.key_for("estuary", 170, "pond") == "estuary-180"
    assert wt.key_for("estuary", None, "pond") == "estuary"
    assert wt.key_for("lake", None, "pond") == "pond" and wt.key_for("ocean", None, "pond") == "sea"


def test_specs_carry_the_true_heading_and_still_types_neither_current_nor_drift():
    r = wt.spec("river-135")
    assert r["edid"] == "ANW_RiverWaterFlow_135" and r["heading"] == 135 and r["speed"] > 0
    assert wt.spec("stream-022")["heading"] == 22.5 and wt.spec("river-337")["heading"] == 337.5   # the key truncates
    assert v.FLOW.search(r["edid"]) and v.FLOW.search(wt.spec("stream-000")["edid"])
    for k in ("sea", "pond", "green-marsh", "blackwater-swamp", "estuary"):
        s = wt.spec(k)
        assert "heading" not in s and s["set"]["LinearVelocity"] == [0, 0, 0], k
        assert not v.FLOW.search(s["edid"]), k   # a still type is never named as flowing water
    est = wt.spec("estuary")["set"]
    assert {est[f"NoiseLayer{n}WindDirection"] for n in ("One", "Two", "Three")} == {270, 30, 150}
    assert set(wt.records(["river-045", "pond"])) == {"river-045", "pond", "sea"}
    assert v.BLEND.match("ANW_WaterBlend_ANW_Water_Pond_10000")   # past 9,999 blend records


def test_off_plane_moves_rounded_vertices_to_their_own_side():
    h = np.array([[3.0, -3.0, 0.0, 9.0, -20.0]])
    steps = np.rint(h / 8).astype(np.int64)
    assert quantize.off_plane(steps, h, 0.0, 8.0) == 3
    assert steps.tolist() == [[1, -1, 1, 1, -2]]
    assert quantize.off_plane(steps, h, 4.0, 8.0) == 0      # a level between steps: nothing can sit on it


def _env():
    return {**os.environ, "DOTNET_ROOT": str(DOTNET), "PATH": f"{DOTNET}:{os.environ['PATH']}",
            "DOTNET_CLI_TELEMETRY_OPTOUT": "1", "DOTNET_NOLOGO": "1"}


@pytest.fixture(scope="module")
def tool():
    if not DOTNET.exists():
        pytest.skip("~/.dotnet is absent")
    out = REPO / "out" / "tools" / "ArgoniaPlugin"
    b = subprocess.run(["dotnet", "build", "-c", "Release", "-o", str(out), "tools/ArgoniaPlugin"], cwd=REPO, env=_env(),
                       capture_output=True, text=True)
    assert b.returncode == 0, b.stdout[-2000:]
    return out / "ArgoniaPlugin.dll"


def test_selftest_noise_heading_head_and_blend(tool):
    r = subprocess.run(["dotnet", str(tool), "waterstudy", "selftest"], cwd=REPO, env=_env(), capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


def test_built_records_differ_and_run_their_way(tool, tmp_path):
    """Every kind's record as Records builds it from the vanilla base, one cell each, far apart: measured, not restated."""
    if not (DATA / "Update.esm").exists():
        pytest.skip("no game data")
    keys = ["sea", "blackwater-swamp", "green-marsh", "pond", "river-045", "stream-202", "estuary-157", "estuary"]
    cells = {f"{i * 20},0": {"water": k, "region": "r"} for i, k in enumerate(keys)}
    (tmp_path / "cells.json").write_text(json.dumps({"cells": cells, "watr": wt.records(keys)}))
    flow = tmp_path / "flow.json"
    flow.write_text(json.dumps([{"cell": [i * 20, 0], "flow_deg": float(k.rsplit("-", 1)[1])}
                                for i, k in enumerate(keys) if k[-1].isdigit()]))
    r = subprocess.run(["dotnet", str(tool), "waterstudy", "plan", str(tmp_path), str(DATA), str(flow), str(tmp_path / "plan.json")],
                       cwd=REPO, env=_env(), capture_output=True, text=True)
    assert r.returncode == 0, r.stdout[-2000:] + r.stderr[-2000:]
    d = json.loads((tmp_path / "plan.json").read_text())
    assert d["own_look_min_pair"] >= wc.MIN_PAIR, d["own_look_pairs"][:3]
    assert d["flowing_cells"] == 3 and d["velocity_within_22_5"] == 3 and d["noise_within_22_5"] == 3, d["flow_examples_off"]
    assert d["still_cells"] == 5 and d["still_cells_with_flow"] == 0
    assert all(k["pure_share"] == 1.0 for k in d["kinds"].values())   # alone, every cell keeps its own record


GOOD = {"kinds": {"sea": {"cells": 10, "pure": 8, "pure_share": 0.8, "near_own_share": 0.9, "reads_as_own_share": 0.9,
                          "own_distance_median": 0, "mean_look": [1] * 10}},
        "own_look_pairs": [["river", "sea", 60.0]], "own_look_min_pair": 60.0, "flowing_cells": 5,
        "velocity_within_22_5": 5, "noise_within_22_5": 5, "velocity_err_p50_p90_max": [5, 10, 11],
        "noise_err_p50_p90_max": [5, 10, 11], "flow_examples_off": [],
        "convention": {"RiverWaterFlowNE": [62, 69, 7], "RiverWaterFlowNW": [316, 335, 20],
                       "CreekWaterFlowSE": [136, 114, 22], "CreekWaterFlowSW": [235, 258, 23]},
        "still_cells": 10, "still_cells_with_flow": 0, "edge_steps": 3, "edge_step_p50_p99_max": [7, 13, 13],
        "shore": {"vertices_near": 10, "within_fight_band": 0, "on_plane": 0, "crossing_edges": 4, "rise_p10_median_p90": [24, 40, 96]}}


def _rows(chk):
    rep = v.Report()
    wc.rows(rep, chk)
    return {r["requirement"].split(" (")[0].split(":")[0]: r["result"] for r in rep.rows}


def test_rows_pass_good_water_and_each_fails_on_its_fault():
    assert set(_rows(GOOD).values()) == {"PASS"}
    bad = {
        "sea": dict(GOOD, kinds={"sea": dict(GOOD["kinds"]["sea"], reads_as_own_share=0.2)}),
        "every two kinds' own looks differ by >= 40 of 255": dict(GOOD, own_look_min_pair=13.0),
        "flowing cells run with the channel graph": dict(GOOD, noise_within_22_5=2),
        "the drift convention holds on Update.esm's river and creek records": dict(GOOD, convention=dict(GOOD["convention"], CreekWaterFlowSW=[235, 55, 180])),
        "still water": dict(GOOD, still_cells_with_flow=3),
        "seams smooth": dict(GOOD, edge_step_p50_p99_max=[4, 22, 34]),
        "no land vertex within the fighting band": dict(GOOD, shore=dict(GOOD["shore"], within_fight_band=33)),
    }
    for row, chk in bad.items():
        res = _rows(chk)
        assert res[row] == "FAIL", row
        assert sum(r == "FAIL" for r in res.values()) == 1, (row, res)
    assert "FAIL" in _rows({k: x for k, x in GOOD.items() if k != "shore"}).values()   # no LAND read: a FAIL, not a pass


def _dist(a, b):
    f = lambda s: [*s["ShallowColor"], *s["DeepColor"], *s["ReflectionColor"], s["Opacity"]]
    return max(abs(x - y) for x, y in zip(f(a), f(b)))


def test_region_variants_keep_kind_identity_and_differ_by_look():
    rs = wt.regions()
    assert len(rs) == 24 and {r["look"] for r in rs.values()} <= set(wt.LOOKS)
    assert wt.split("river-045@nha-enasa") == ("river", "045", "nha-enasa") and wt.split("pond@aphon-isle") == ("pond", "", "aphon-isle")
    assert wt.split("sea") == ("sea", "", "") and wt.plain_key("river-045@nha-enasa") == "river-045"
    assert wt.key_for("lake", None, "pond", "aphon-isle") == "pond@aphon-isle"
    assert wt.key_for("river", 50, "pond", "nha-enasa") in ("river-045@nha-enasa", "river-045")
    assert wt.key_for("lake", None, "pond", "no-such-region") == "pond" and wt.key_for("lake", None, "pond") == "pond"
    plain = {k: wt.spec(k)["set"] for k in wt.KINDS if k not in wt.RUNNING}
    seen = set()
    for rid, r in rs.items():
        for kind in plain:
            key = wt.variant_key(kind, rid)
            if key == kind:
                assert wt.toward(wt.KINDS[kind]["set"], r["look"]) == wt.KINDS[kind]["set"]
                continue
            s = wt.spec(key)
            assert s["copy"] == wt.KINDS[kind]["copy"] and s["edid"].endswith(f"_R{r['slot']:02d}") and len(s["edid"]) <= 40
            assert s["set"]["LinearVelocity"] == [0, 0, 0] and not v.FLOW.search(s["edid"])
            seen.add(s["edid"])
            assert s["set"] != wt.KINDS[kind]["set"]
            # every variant still reads as its own kind: nearer its own plain record than any other kind's
            own = _dist(s["set"], plain[kind])
            assert all(own < _dist(s["set"], o) for k, o in plain.items() if k != kind), (key, own)
    assert len(seen) == len({e for e in seen})
    run = wt.spec("river-135@nha-enasa")
    assert run["heading"] == 135 and run["speed"] > 0 and v.FLOW.search(run["edid"]) and run["edid"].endswith("_R14")
    # two regions with different looks differ; the same look is the same colour
    a, b = wt.spec("pond@aphon-isle")["set"], wt.spec("pond@barsaebica")["set"]
    assert a["ShallowColor"] != b["ShallowColor"]


def test_records_carry_the_plain_record_of_each_variant_and_the_neutral_sea():
    keys = wt.records(["pond@aphon-isle", "river-045@nha-enasa"])
    assert {"sea", "pond", "river-045", "pond@aphon-isle", "river-045@nha-enasa"} == set(keys)
    assert keys["sea"] == wt.spec("sea") and "look" not in keys["sea"]
    assert len({k["edid"] for k in keys.values()}) == len(keys)


def test_running_kinds_read_as_their_own_kind_in_every_region():
    plain = {k: wt.KINDS[k]["set"] for k in wt.KINDS}
    for rid, r in wt.regions().items():
        for kind in wt.KINDS:
            s = wt.toward(wt.KINDS[kind]["set"], r["look"])
            own = _dist(s, plain[kind])
            assert all(own < _dist(s, o) for k, o in plain.items() if k != kind), (kind, rid, own)
