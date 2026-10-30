"""L1/L2 for tools/world_sample.py: the world sample's journey and scenes are what the data gives, cover the 13 stops
in order, end each scene on its travel line, and use weathers from each stop's own region list (never SkyrimClear)."""
import re
import sys
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from tools import run_journey as rj  # noqa: E402
from tools import world_sample as ws  # noqa: E402

JOURNEY = yaml.safe_load(ws.JOURNEY.read_text())
STOPS = JOURNEY["stops"]


def scene_lines(stop):
    text = (ws.SCENES / f"{stop['scene']}.txt").read_bytes().decode()
    assert "\r\n" in text and "\n" not in text.replace("\r\n", "")
    return [ln for ln in text.splitlines() if ln and not ln.startswith(";")]


def test_the_journey_validates_and_has_thirteen_stops_in_order():
    assert "world-sample.yaml" in rj.dry(ws.JOURNEY)
    assert [s["n"] for s in STOPS] == list(range(1, 14))
    order = [int(re.match(r"s(\d\d)-", st["name"]).group(1)) for st in JOURNEY["steps"]]
    assert order == sorted(order) and set(order) == set(range(1, 14))


def test_each_scene_ends_on_its_travel_line_and_sets_time_and_a_region_weather():
    for s in STOPS:
        lines = scene_lines(s)
        assert re.match(r"(cow ARG_Province -?\d+ -?\d+|player\.moveto ARG_Ref_\w+)$", lines[-1]), (s["scene"], lines[-1])
        assert any(ln.startswith("set gamehour to") for ln in lines[:-1])
        weather = [ln for ln in lines[:-1] if ln.split()[0] in ("fw", "sw")]
        assert len(weather) == 1 and weather[0].split()[1] == s["weather"]
        assert "0000081A" not in " ".join(lines).upper() and s["weather"] != "SkyrimClear"


def test_travel_lines_after_the_first_are_run_by_the_journey_with_a_wait():
    for s in STOPS[1:]:
        arrive = next(st for st in JOURNEY["steps"] if st["name"] == f"s{s['n']:02d}-arrive")
        assert arrive["do"][0] == {"console": f"bat {s['scene']}"} and arrive["do"][1]["wait"] <= 10


def test_numbers_decide_where_the_brief_says():
    steps = {st["name"]: st for st in JOURNEY["steps"]}
    probes = [st for st in steps.values() if "expected_ground_m" in st]
    assert len(probes) >= 15
    for st in probes:  # a window of +-0.5 m around the ground, or a wider one only for water stops
        z = [e for e in st["expect"] if e.get("path") == "pos.z"]
        lo = next(e["ge"] for e in z if "ge" in e)
        hi = next(e["le"] for e in z if "le" in e)
        assert lo < hi
    assert {n for n in steps if n.endswith("frametime")} == {"s08-frametime", "s13-frametime"}
    assert sum(n.startswith("s12-path-") for n in steps) >= 21
    assert "quests_running" in str(steps["s11-quarantine"]) and "music" in str(steps["s11-quarantine"])
    assert {f"s11-day-{d}" for d in range(8)} <= set(steps)
    assert any("reader" in st for st in steps.values())
    for n in (1, 2, 3, 4, 5, 6, 7, 8, 10, 13):
        assert any("reader" in st for k, st in steps.items() if k.startswith(f"s{n:02d}-")), n
    for st in steps.values():
        if "owed" in st:
            assert st["owed"].strip()


def test_the_probe_window_is_half_a_metre_each_way():
    class G:
        import numpy as np
        H = np.array([[10.0]])

        def units(self, r, c):
            return 1.0, 2.0, 700.0
    st = ws.probe_step(G(), "p", 0, 0, "why")
    tol = 0.5 * 70.03
    z = [e for e in st["expect"]]
    assert z[0]["ge"] == pytest.approx(700.0 - tol, abs=0.01) and z[1]["le"] == pytest.approx(700.0 + tol, abs=0.01)
    assert st["do"][0]["teleport"] == "pos 1.0 2.0 800.0"


@pytest.mark.skipif(not (ws.data_root() / "terrain" / "refined-height-f32.npy").exists()
                    or not (REPO / "out" / "water" / "plan.json").exists()
                    or not (REPO / "out" / "navmesh" / "claywater" / "navm").exists(),
                    reason="the terrain, water and navmesh data are not on this machine")
def test_the_files_on_disk_are_what_the_data_gives():
    files = ws.render()
    assert len(files) == 15  # 13 scenes, the world sample, the road hops
    for path, text in files.items():
        assert path.read_bytes().decode() == text, f"{path.name} is stale: run tools/world_sample.py --write"
    for s in ws.build():
        assert s["weather"]["edid"] in s["weather"]["list"] and s["weather"]["id"] != "clear"


def test_the_falls_stop_counts_the_resolved_falls_piece():
    """The stop finds its falls by the piece resolver's key, not a record named in the generator: it must see the
    placed falls pieces (a hard-coded Dawnguard key once left it counting none, and top_z fell to the mist's)."""
    import json
    keys = ws.piece_keys()
    assert keys["falls"] != keys["mist"]
    placed = {r["base"] for line in (ws.REPO / "out" / "water" / "cells.jsonl").read_text().splitlines()
              for r in json.loads(line)["refs"]}
    assert keys["falls"] in placed and keys["mist"] in placed
    assert [s for s in STOPS if s["n"] == 5][0]["falls"]["pieces_near"] >= 1


def test_road_hops_every_100_m_with_the_end_and_skyrim_ltex_ids():
    from tools import world_sample as ws
    hops = ws._along([(0.0, 0.0), (250.0, 0.0), (250.0, 30.0)], 100.0)
    assert [round(h[2]) for h in hops] == [0, 100, 200, 280]
    assert hops[-1][:2] == (250.0, 30.0)
    assert ws._along([(0.0, 0.0), (90.0, 0.0)], 100.0)[-1][2] == 90.0
    assert ws._ltex_id("0B424C:Skyrim.esm") == "000B424C"
    import pytest
    with pytest.raises(ValueError):
        ws._ltex_id("000801:Argonia.esm")


def test_the_road_hops_journey_is_generated_and_validates():
    import yaml
    from tools import run_journey as rj
    from tools import world_sample as ws
    j = yaml.safe_load(ws.ROAD_HOPS.read_text())
    assert ws.ROAD_HOPS.read_text().startswith("# 2.W3 §b") and "GENERATED by tools/world_sample.py" in ws.ROAD_HOPS.read_text()
    assert len(j["legs"]) == 23 and not any("owed" in s for s in j["steps"])
    assert all(any(e.get("read") == ["ltex"] for e in s["expect"]) for s in j["steps"][1:-1])
    assert j["steps"][-1]["name"] == "tear-road-stage"
    assert "ok" in rj.dry(ws.ROAD_HOPS)
