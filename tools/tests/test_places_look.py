"""The look tool's pure parts (tools/places/look/geom.py): framing and projection, picking, the section camera and
which pieces a section crosses, the walking route, and probe's rules for floating, resting, hanging and span ends;
plus one smoke test of the browser view, skipped where no browser is installed."""
import math
import os
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from tools.places import xform
from tools.places.look import geom


class Flat:
    """Ground at one height everywhere, water at another (or none)."""
    def __init__(self, z=0.0, water=None):
        self.z, self.w = z, water

    def height(self, x, y):
        return self.z

    def water(self, x, y):
        return self.w


def piece(pid, pos, lo, hi, kind="static", rot=(0, 0, 0), edid="Thing", **kw):
    return {"id": pid, "base": "B:" + pid, "kind": kind, "edid": edid, "model": f"m/{edid}.nif", "resolved": True,
            "m": xform.matrix(list(pos), list(rot), 1.0), "lo": list(lo), "hi": list(hi), **kw}


# ---------- framing and projection ----------
@pytest.mark.parametrize("side", ["n", "e", "se", "sw"])
def test_frame_fills_and_centres(side):
    lo, hi = [0, 0, 0], [400, 200, 300]
    cam = geom.frame(lo, hi, side, "oblique", 768, 576)
    c = geom.corners({"m": xform.matrix([0, 0, 0], [0, 0, 0]), "lo": lo, "hi": hi})
    px = geom.project(cam, c)
    assert (px[:, 2] > 0).all()
    assert px[:, 0].min() >= 0 and px[:, 0].max() <= 768 and px[:, 1].min() >= 0 and px[:, 1].max() <= 576
    # the box fills a fair share of the frame, and its middle lands near the frame's middle
    assert (px[:, 0].max() - px[:, 0].min()) > 768 * 0.35 or (px[:, 1].max() - px[:, 1].min()) > 576 * 0.35
    mid = geom.project(cam, [[200, 100, 150]])[0]
    assert abs(mid[0] - 384) < 2 and abs(mid[1] - 288) < 2
    # the camera stands on the named side
    az = math.degrees(math.atan2(cam["pos"][1] - 100, cam["pos"][0] - 200))
    assert abs((az - geom.SIDES[side] + 180) % 360 - 180) < 1


def test_frame_eye_and_top():
    eye = geom.frame([0, 0, 0], [400, 400, 300], "s", "eye", ground_z=0)
    assert eye["pos"][2] == pytest.approx(geom.EYE) and eye["pos"][1] < 0
    top = geom.frame([0, 0, 0], [400, 400, 300], "s", "top")
    assert top["up"] == [0.0, 1.0, 0.0] and top["pos"][:2] == [200, 200]
    # from above, north is up the image
    a, b = geom.project(top, [[200, 200, 0], [200, 300, 0]])
    assert b[1] < a[1] and abs(b[0] - a[0]) < 1e-6


def test_ray_inverts_project_and_pick_finds_nearest():
    cam = geom.frame([0, 0, 0], [1000, 1000, 400], "se", "oblique")
    near = piece("near", [500, 500, 0], [-50, -50, 0], [50, 50, 100])
    far = piece("far", [-2000, 3000, 0], [-50, -50, 0], [50, 50, 100])
    px = geom.project(cam, [[500, 500, 50]])[0]
    o, d = geom.ray(cam, px[0], px[1])
    q = o + d * px[2] / float(np.dot(d, -geom.axes(cam)[2]))
    assert np.allclose(q, [500, 500, 50], atol=1e-6)
    hits = geom.pick(cam, px[0], px[1], [far, near])
    assert hits and hits[0][1]["id"] == "near"
    assert geom.pick(cam, 2, 2, [near]) == []


def test_nice_and_hull():
    assert geom.nice(730) == 500 and geom.nice(0.3) == 0.2 and geom.nice(2000) == 2000
    assert set(geom.hull([(0, 0), (1, 0), (1, 1), (0, 1), (0.5, 0.5)])) == {(0, 0), (1, 0), (1, 1), (0, 1)}


# ---------- section ----------
def test_section_camera_square_scale_and_slab():
    a, b = [0, 0], [1000, 0]
    cam = geom.section_camera(a, b, -100, 500, 768, 576, slab=50)
    pa, pb = geom.project(cam, [[0, 0, 0], [1000, 0, 0]])
    assert pa[0] < pb[0]                                       # A on the left
    up = geom.project(cam, [[0, 0, 100]])[0]
    assert (pb[0] - pa[0]) / 1000 == pytest.approx((pa[1] - up[1]) / 100, rel=1e-6)   # one scale both ways
    keep = lambda p: all(np.dot(pl[:3], p) + pl[3] >= 0 for pl in cam["clip"])   # noqa: E731
    assert keep([500, 49, 0]) and keep([500, -49, 0]) and not keep([500, 80, 0]) and not keep([500, -80, 0])


def test_crosses_and_profile():
    on = piece("on", [500, 30, 0], [-20, -20, 0], [20, 20, 50])
    off = piece("off", [500, 400, 0], [-20, -20, 0], [20, 20, 50])
    past = piece("past", [1500, 0, 0], [-20, -20, 0], [20, 20, 50])
    assert geom.crosses(on, [0, 0], [1000, 0], 96)
    assert not geom.crosses(off, [0, 0], [1000, 0], 96) and not geom.crosses(past, [0, 0], [1000, 0], 96)
    prof = geom.profile(Flat(7, 10), [0, 0], [100, 0], step=25)
    assert len(prof) == 5 and prof[-1] == (100.0, 7, 10)


def test_long_axis_of_a_turned_span():
    span = piece("s", [0, 0, 0], [-300, -50, 0], [300, 50, 20], rot=(0, 0, math.pi / 2))
    a, b = geom.long_axis(span, extra=100)
    assert abs(a[0]) < 1e-6 and abs(b[0]) < 1e-6 and abs(abs(a[1] - b[1]) - 800) < 1e-6


# ---------- probe ----------
def test_floating_resting_and_chains():
    g = Flat(0)
    post = piece("post", [0, 0, 0], [-10, -10, -20], [10, 10, 400])          # stands in the ground
    deck = piece("deck", [0, 0, 400], [-200, -200, 0], [200, 200, 20])       # rests on the post's top
    hut = piece("hut", [0, 0, 420], [-150, -150, 0], [150, 150, 300], kind="building")
    lone = piece("lone", [2000, 0, 300], [-200, -200, 0], [200, 200, 20])    # a deck in the air
    on_lone = piece("onlone", [2000, 0, 320], [-50, -50, 0], [50, 50, 80])  # rests on the deck in the air
    f = {x["id"]: x for x in geom.faults([post, deck, hut, lone, on_lone], g) if x["fault"] == "floats"}
    assert set(f) == {"lone", "onlone"}
    assert f["lone"]["over"] == pytest.approx(300) and "nothing under it" in f["lone"]["why"]
    assert f["onlone"]["on"] == ["lone"] and "do not reach the ground" in f["onlone"]["why"]


def test_a_roof_far_above_holds_nothing_and_trees_hold_only_hangers():
    g = Flat(0)
    house = piece("house", [0, 0, 0], [-300, -300, 0], [300, 300, 800], kind="building")
    deck = piece("deck", [0, 0, 300], [-50, -50, 0], [50, 50, 20])          # inside the house's box, far under its top
    tree = piece("tree", [3000, 0, 0], [-300, -300, 0], [300, 300, 2000], kind="tree")
    lantern = piece("lantern", [3000, 0, 1500], [-10, -10, -60], [10, 10, 0], kind="clutter", edid="LanternHang")
    plank = piece("plank", [3000, 200, 1500], [-80, -20, 0], [80, 20, 10], edid="Plank")    # in the canopy, on nothing
    ids = {x["id"] for x in geom.faults([house, deck, tree, lantern, plank], g) if x["fault"] == "floats"}
    assert ids == {"deck", "plank"}


def test_span_ends_doors_and_unresolved():
    g = Flat(0)
    bridge = piece("br", [0, 0, 300], [-400, -60, 0], [400, 60, 30], edid="DocksideBridge01")
    post = piece("post", [-400, 0, 0], [-15, -15, -10], [15, 15, 300])
    door = piece("door", [5000, 0, 400], [-60, -10, 0], [60, 10, 200], kind="door",
                 door={"to_space": "Hut", "arrival": [5000, -120, 400]})
    box = dict(piece("box", [8000, 0, 0], [0, 0, 0], [10, 10, 10]), resolved=False)
    missing = {"id": "gone", "base": "X:1", "kind": "static", "missing": True, "model": None, "resolved": False,
               "m": xform.matrix([0, 0, 0], [0, 0, 0]), "lo": [0, 0, 0], "hi": [1, 1, 1]}
    f = geom.faults([bridge, post, door, box, missing], g)
    ends = [x for x in f if x["fault"] == "unsupported end"]
    assert len(ends) == 1 and ends[0]["at"][0] == pytest.approx(400)          # the far end only
    assert any(x["fault"] == "no ground at door" and x["id"] == "door" for x in f)
    assert any(x["fault"] == "unresolved" and x["id"] == "box" for x in f)
    assert any(x["fault"] == "missing base" and x["id"] == "gone" for x in f)


def test_a_ship_holds_its_deck_and_stage_made_pieces_are_not_missing():
    g = Flat(0)
    ship = piece("ship", [0, 0, -200], [-600, -150, 0], [600, 150, 900], kind="building", edid="0ShipImperial",
                 model="architecture/ships/imperialship01base.nif")
    door = piece("door", [0, 0, 280], [-60, -10, 0], [60, 10, 200], kind="door")    # on the deck, rigging far above
    gone = {"id": "p.sap.T", "base": "Mod.esp:1", "kind": "activator", "missing": True, "model": None, "resolved": False,
            "m": xform.matrix([0, 0, 0], [0, 0, 0]), "lo": [0, 0, 0], "hi": [1, 1, 1]}
    chest = dict(gone, id="p.C", base="Skyrim.esm:0267E7")
    real = dict(gone, id="p.R", base="Mod.esp:2")
    f = geom.faults([ship, door, gone, chest, real], g)
    assert [(x["id"], x["fault"]) for x in f] == [("p.R", "missing base")]


class Slope(Flat):
    """Ground rising 1 unit per unit of x."""
    def height(self, x, y):
        return float(x)


def test_a_rock_half_in_a_bank_shows_and_the_stolen_goods_chest_is_out_of_reach():
    g = Slope()
    rock = piece("rock", [0, 0, -100], [-400, -100, 0], [400, 100, 200], kind="rock")       # top 100; ground -400..400
    chest = piece("chest", [3000, 0, 0], [-40, -30, 0], [40, 30, 60], kind="container", edid="EvidenceChestStolenGoods")
    sunk = piece("sunk", [3000, 500, 0], [-40, -30, 0], [40, 30, 60], kind="container", edid="Chest01")
    assert {x["id"] for x in geom.faults([rock, chest, sunk], g) if x["fault"] == "buried"} == {"sunk"}


def test_wall_fixed_things_are_held_and_a_lantern_in_mid_air_is_not():
    g = Flat(0)
    house = piece("house", [0, 0, 0], [-300, -300, 0], [300, 300, 400], kind="building")
    lamp = piece("lamp", [0, -310, 250], [-10, -15, -30], [10, 15, 30], kind="clutter", edid="CandleLantern01")  # on the wall
    win = piece("win", [305, 0, 200], [-6, -40, -40], [6, 40, 40], edid="MudWindow01")                           # in the wall
    stray = piece("stray", [2000, 0, 300], [-10, -10, -30], [10, 10, 30], kind="clutter", edid="CandleLantern01")
    assert {x["id"] for x in geom.faults([house, lamp, win, stray], g) if x["fault"] == "floats"} == {"stray"}


def test_a_plant_is_buried_only_when_most_of_it_is_under():
    g = Flat(0)
    weed = piece("weed", [0, 0, -10], [-20, -20, 0], [20, 20, 30], kind="plant", edid="Nchickweed")  # root 10 under
    gone = piece("gone", [500, 0, -40], [-20, -20, 0], [20, 20, 50], kind="plant", edid="Braken")    # 40 of 50 under
    assert {x["id"] for x in geom.faults([weed, gone], g) if x["fault"] == "buried"} == {"gone"}


def test_probe_piece_feet_and_neighbours():
    g = Flat(10)
    a = piece("a", [0, 0, 0], [-50, -50, 0], [50, 50, 100])
    b = piece("b", [130, 0, 0], [-50, -50, 0], [50, 50, 100])
    r = geom.probe_piece(a, g, [a, b])
    assert r["feet_over_ground"] == [-10, -10] and r["lowest_over_ground"] == -10
    assert r["neighbours"][0] == {"id": "b", "gap": 30.0}


def test_buried():
    g = Flat(0)
    deep = piece("deep", [0, 0, -3000], [-50, -50, 0], [50, 50, 100], kind="building")
    sunk = piece("sunk", [500, 0, -40], [-50, -50, 0], [50, 50, 100], kind="building")
    f = {x["id"]: x["fault"] for x in geom.faults([deep, sunk], g)}
    assert f == {"deep": "buried"}


# ---------- walking ----------
def test_route_joins_paths_and_stations():
    p1 = [[0, 0], [1000, 0]]
    p2 = [[1050, 50], [1050, 1000]]                       # starts within the join distance of p1's end
    way = geom.route([p1, p2], [0, -10], [1050, 990])
    assert way[1] == [0.0, 0.0] and way[-2] == [1050.0, 1000.0]
    st = geom.stations(way, 4)
    assert len(st) == 4 and st[0][1] == pytest.approx([0, -1], abs=1e-6) or st[0][1][0] >= 0
    assert all(abs(math.hypot(*d) - 1) < 1e-6 for _, d in st)


# ---------- the browser ----------
CHROME = Path.home() / ".cache" / "ms-playwright"


@pytest.mark.skipif(not CHROME.exists() or not shutil.which("python3"), reason="no headless browser installed")
def test_browser_smoke(tmp_path):
    """The agent view loads a real place and draws a look (slow: software GL; skipped without a browser or place)."""
    pytest.importorskip("playwright")
    from tools.places.look.scene import data_out
    if os.environ.get("LOOK_SMOKE") != "1" or not (data_out() / "bundles" / "ground.jal-veesa").exists():
        pytest.skip("set LOOK_SMOKE=1 on a machine with the place bundles to run the browser smoke test")
    env = dict(os.environ, LOOK_OUT=str(tmp_path), LOOK_PORT="8797", LOOK_IDLE="120")
    run = lambda *a: subprocess.run([sys.executable, "-m", "tools.places", "look", *a], env=env, capture_output=True, text=True, timeout=600)  # noqa: E731
    try:
        r = run("jal-veesa", "at", "b01", "--size", "320x240")
        assert r.returncode == 0, r.stdout + r.stderr
        import json
        png = json.loads(r.stdout)["png"]
        from PIL import Image
        im = np.asarray(Image.open(png).convert("L"), float)
        assert im.shape == (240, 320) and im.std() > 10           # drawn, not a blank frame
    finally:
        run("stop")
