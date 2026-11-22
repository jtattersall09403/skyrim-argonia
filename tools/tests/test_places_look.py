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

from tools.places import shape, xform

shape.REAL = False   # measure the fixtures by their boxes (registered meshes only): no converted model is read
from tools.places.look import framing, geom


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
    assert len(ends) == 1 and ends[0]["at"][0] == pytest.approx(400, abs=2)          # the far end only
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
    bank = piece("bank", [-1000, 0, -1010], [-20, -20, 0], [20, 20, 30], kind="plant", edid="Nchickweed")  # on a slope
    assert {x["id"] for x in geom.faults([weed, gone], g) if x["fault"] == "buried"} == {"gone"}
    assert not [x for x in geom.faults([bank], Slope()) if x["fault"] == "buried"]


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


def test_commit_writes_strokes_as_agent_edits_and_spares_the_owners_rows(tmp_path, monkeypatch):
    """`look <place> commit`: the session's strokes go into the place files by the studio's apply, as the agent's
    save (agent-edits/, agent_saves_applied), never over a row an owner's finalised save touched; the session empties."""
    import json
    from tools.places import edits
    from tools.places.look import daemon, verbs
    src = Path(__file__).resolve().parents[2] / "newworld" / "places" / "jal-veesa"
    places = tmp_path / "places"
    shutil.copytree(src, places / "jal-veesa")
    pdir = places / "jal-veesa"
    monkeypatch.setattr(daemon, "LOOK_OUT", tmp_path / "look")
    refs = [r for r in edits.load_place(pdir)["spaces"]["exterior"]["refs"] if not r.get("removed")]
    a, b, c = refs[0], refs[1], refs[2]
    (pdir / "edits").mkdir(exist_ok=True)
    (pdir / "edits" / "owner.json").write_text(json.dumps({"save_id": "owner", "final": True, "ops": [{"id": c["id"]}]}))

    def mv(r, dz):
        return {"op": "ref.move", "space": "exterior", "id": r["id"], "call": "fault",
                "before": {"pos": r["pos"]}, "after": {"pos": [r["pos"][0], r["pos"][1], r["pos"][2] + dz]}}
    sess = {"strokes": [[mv(a, -10)], [{"op": "ref.remove", "space": "exterior", "id": b["id"], "call": "fault",
                                        "before": b}], [mv(c, -5)]], "snapshots": {"x": []}, "n": 0}
    with pytest.raises(ValueError):
        verbs.commit("jal-veesa", dict(sess), [], places=places)
    res = verbs.commit("jal-veesa", sess, ["-m", "seat a"], places=places)
    assert res["left_for_owner"] == [{"stroke": 3, "owner_rows": [c["id"]], "why": "refused: it carries no note it answers"}]
    assert "REFUSED" in res["warning"]
    after = {r["id"]: r for r in edits.load_place(pdir)["spaces"]["exterior"]["refs"]}
    assert after[a["id"]]["pos"][2] == pytest.approx(a["pos"][2] - 10)
    assert b["id"] not in after or after[b["id"]].get("removed")
    assert after[c["id"]]["pos"] == c["pos"]
    place = json.loads((pdir / "place.json").read_text())
    assert place["agent_saves_applied"] and not place.get("saves_applied")
    saved = json.loads((pdir / "agent-edits" / f"{place['agent_saves_applied'][-1]}.json").read_text())
    assert saved["by"] == "agent" and saved["name"] == "seat a" and not saved["final"]
    assert sess["strokes"] == [] and sess["snapshots"] == {}


def test_a_boat_on_the_water_floats_and_one_in_the_air_does_not():
    g = Flat(-200, water=0.0)
    hull = dict(lo=[-150, -50, 0], hi=[150, 50, 120], kind="building", edid="ShipRowBoat01",
                model="dungeons/ship/shiprowboat01.nif")
    afloat = piece("afloat", [0, 0, -25], **{k: v for k, v in hull.items() if k in ("lo", "hi")},
                   **{k: v for k, v in hull.items() if k not in ("lo", "hi")})
    flying = piece("flying", [900, 0, 300], **{k: v for k, v in hull.items() if k in ("lo", "hi")},
                   **{k: v for k, v in hull.items() if k not in ("lo", "hi")})
    assert [(x["id"], x["fault"]) for x in geom.faults([afloat, flying], g)] == [("flying", "floats")]


# ---------- the built walkable mesh ----------
def _two_decks(step=0.0, across=0.0):
    """Two 100x100 squares of two triangles each: the second shifted `across` along x past the first's edge and
    raised `step`; joined (one island) only when they touch at the same height."""
    v = [[0, 0, 0], [100, 0, 0], [100, 100, 0], [0, 100, 0],
         [100 + across, 0, step], [200 + across, 0, step], [200 + across, 100, step], [100 + across, 100, step]]
    t = [[0, 1, 2], [0, 2, 3], [4, 5, 6], [4, 6, 7]]
    key = [tuple(p) for p in v]
    edges = {}
    for i, tri in enumerate(t):
        for k in range(3):
            edges.setdefault(frozenset((key[tri[k]], key[tri[(k + 1) % 3]])), []).append(i)
    nb = [[next((o for o in edges[frozenset((key[tri[k]], key[tri[(k + 1) % 3]]))] if o != i), -1) for k in range(3)]
          for i, tri in enumerate(t)]
    return v, t, nb


def test_mesh_islands_and_a_join():
    from tools.places.look import mesh
    M = mesh.Mesh(*_two_decks())
    assert len(M.count) == 1 and M.island_of(50, 50, 0) == M.island_of(150, 50, 0)


def test_mesh_gap_a_height_step():
    from tools.places.look import mesh
    M = mesh.Mesh(*_two_decks(step=80))
    a, b = M.island_of(50, 50, 0), M.island_of(150, 50, 80)
    assert a != b and a >= 0 and b >= 0
    g = M.gap(a, b)
    assert g["kind"] == "height step" and g["step"] == 80 and g["across"] == 0 and g["at"][0] == 100


def test_mesh_gap_a_missing_strip():
    from tools.places.look import mesh
    M = mesh.Mesh(*_two_decks(across=60))
    g = M.gap(M.island_of(50, 50), M.island_of(200, 50))
    assert g["kind"] == "missing strip" and g["across"] == 60 and g["step"] == 0


def test_mesh_point_off_and_on_by_height():
    from tools.places.look import mesh
    M = mesh.Mesh(*_two_decks(step=300))
    assert M.tri_at(150, 50, 0)[0] == -1          # the upper deck is far over a point on the ground
    assert M.tri_at(150, 50, 290)[1] == pytest.approx(300)


def test_mesh_stale_when_a_place_file_is_newer(tmp_path):
    from tools.places.look import mesh
    plan = tmp_path / "b" / "shards" / "p" / "plan.json"
    plan.parent.mkdir(parents=True)
    plan.write_text("{}")
    pd = tmp_path / "p"
    (pd / "spaces").mkdir(parents=True)
    f = pd / "spaces" / "refs.jsonl"
    f.write_text("")
    os.utime(f, (plan.stat().st_mtime + 10, plan.stat().st_mtime + 10))
    assert mesh.stale(pd, tmp_path / "b", "p")["stale"]
    os.utime(f, (plan.stat().st_mtime - 10, plan.stat().st_mtime - 10))
    assert not mesh.stale(pd, tmp_path / "b", "p")["stale"]


# ---------- inside a room (room.py) ----------
def _square_floor(z=0.0, size=1000.0):
    from tools.places.look import room
    return room.Floor([[0, 0, z], [size, 0, z], [size, size, z], [0, size, z]], [[0, 1, 2], [0, 2, 3]])


def test_stacked_floors_measure_a_piece_against_the_floor_under_it():
    from tools.places.look import room
    v = [[0, 0, 0], [1000, 0, 0], [1000, 1000, 0], [0, 1000, 0],
         [0, 0, 250], [1000, 0, 250], [1000, 1000, 250], [0, 1000, 250]]
    f = room.Floor(v, [[0, 1, 2], [0, 2, 3], [4, 5, 6], [4, 6, 7]])    # a hold floor under a deck
    assert f.height(500, 500) == pytest.approx(250)                   # the walkable top, as before
    assert f.height_below(500, 500, 10) == pytest.approx(0)            # a crate on the hold floor
    assert f.height_below(500, 500, 255) == pytest.approx(250)         # a barrel on the deck
    assert f.height_below(500, 500, -200) == pytest.approx(0)          # under every floor: the lowest
    lower = [[2000, 0, 0], [3000, 0, 0], [3000, 1000, 0], [2000, 1000, 0]]     # the hold floor walked beside the deck
    hold = room.Floor(v + lower, [[4, 5, 6], [4, 6, 7], [8, 9, 10], [8, 10, 11], [0, 1, 2]])
    assert hold.height_below(200, 800, 10) is None       # at floor level under the deck, no hold floor walked there
    assert hold.height_below(200, 800, -300) == pytest.approx(250)    # in the bilge: against the floor over it
    cargo = room.Floor(v[:4] + [[2000, 0, -200], [3000, 0, -200], [3000, 1000, -200]], [[0, 1, 2], [0, 2, 3], [4, 5, 6]])
    assert cargo.height_below(500, 500, -150) is None    # a crate on the lower cargo deck, its mesh cut round the stack
    assert f.height_below(1500, 500, 0) is None


def test_room_names_floor_and_navmesh_rows(tmp_path):
    from tools.places.look import room
    spaces = {"exterior": {"space": None}, "HutA": {"space": {"name": "Vosh-Leera's House"}},
              "HallB": {"space": {"name": "Great Hall"}}}
    assert room.space_id(spaces, "vosh-leera's house") == "HutA"
    assert room.space_id(spaces, "hallb") == "HallB" and room.space_id(spaces, "outside") == "exterior"
    with pytest.raises(KeyError, match="HallB"):
        room.space_id(spaces, "Cellar")
    f = _square_floor(50)
    assert f.height(500, 500) == pytest.approx(50) and f.height(1500, 500) is None and f.water(0, 0) is None
    nav = tmp_path / "navmesh.jsonl"
    nav.write_text('{"verts": [[0,0,0],[100,0,0],[0,100,0],[5000,0,0],[5100,0,0],[5000,100,0]], '
                   '"tris": [[0,1,2,0,0],[3,4,5,0,0]]}\n')
    assert len(room.floor_of(nav).T) == 2
    assert len(room.floor_of(nav, {"box": [-50, -50, 400, 400]}).T) == 1   # a cut keeps its own floor only


def test_a_camera_inside_a_room_stops_at_the_floors_edge_and_at_a_wall():
    from tools.places.look import room
    f = _square_floor()
    got = room.stand_inside(f, [500, 500], [1, 0], 2000)
    assert 400 <= got <= 500                       # the floor ends 500 east of the target
    wall = [(700, 0, 720, 1000, 0, 300)]
    assert room.stand_inside(f, [500, 500], [1, 0], 2000, blocks=wall) < 200
    assert room.stand_inside(f, [500, 500], [-1, 0], 300) == 300   # the floor goes on: the whole distance


def test_kit_pieces_fixed_to_the_shell_are_held_and_a_lone_floater_is_not():
    from tools.places.look import room
    g = Flat(0)
    wall = piece("wall", [0, 0, 0], [0, -200, 0], [20, 200, 600], kind="building")
    arch = piece("arch", [30, 0, 400], [-10, -100, 0], [10, 100, 100], kind="building")   # set into the wall
    lone = piece("lone", [600, 0, 300], [-50, -50, 0], [50, 50, 40], kind="furniture")    # a bench in the air
    f = geom.faults([wall, arch, lone], g)
    assert {x["id"] for x in f if x["fault"] == "floats"} == {"arch", "lone"}
    assert {x["id"] for x in room.held_by_shell(f, [wall, arch, lone]) if x["fault"] == "floats"} == {"lone"}


def test_openings_onto_the_void_are_placed_where_the_way_out_meets_the_room():
    from tools.places.look import room
    looks = [{"at": [100, 500, 100], "out": [{"face": "w", "frac": 0.6, "dir": [-1, 0, 0]},
                                              {"face": "up", "frac": 0.001, "dir": [0, 0, 1]}]},
             {"at": [150, 520, 100], "out": [{"face": "w", "frac": 0.3, "dir": [-1, 0, 0]}]},
             {"at": [500, 500, 100], "out": []}]
    o = room.openings(looks, [0, 0, 1000, 1000])
    assert len(o) == 1 and o[0]["towards"] == "west" and o[0]["edge_at"][0] == 0 and len(o[0]["seen_from"]) == 2
    assert room.heading([0, 0, 1]) == "up" and room.heading([0, 1, 0.5]) == "north and up"
    pts = room.spread(np.array([[0, 0, 0], [1, 0, 0], [1000, 0, 0], [0, 1000, 0]], float), 3)
    assert len(pts) == 3 and {tuple(p[:2]) for p in pts} >= {(1000.0, 0.0), (0.0, 1000.0)}


def test_a_room_copied_from_another_source_is_read_from_that_source_and_kept_to_its_cut(tmp_path):
    """The draft bundle (what the studio and the look tool draw) reads a room added from another place of our mods
    from the bundle its copy_of names, and keeps only what lies in its cut."""
    import json as _json
    from tools.places import draft_bundle
    own, other = tmp_path / "src.own", tmp_path / "src.other"
    for b in (own, other):
        (b / "spaces" / "Hall").mkdir(parents=True)
    (own / "spaces" / "Hall" / "refs.jsonl").write_text("")
    rows = [{"id": "a", "base": "B:a", "pos": [100, 100, 0]}, {"id": "b", "base": "B:b", "pos": [5000, 100, 0]},
            {"id": "c", "base": "B:c", "pos": [200, 200, 0], "kind": "actor"}]
    (other / "spaces" / "Hall" / "refs.jsonl").write_text("".join(_json.dumps(r) + "\n" for r in rows))
    info = {"copy_of": "other/Hall", "cut": {"box": [0, 0, 1000, 1000]}}
    assert draft_bundle.copy_src(info, own) == other
    got = draft_bundle.copy_space(info, [{"id": "new", "base": "B:n", "pos": [1, 1, 0]}], draft_bundle.copy_src(info, own))
    assert sorted(r["id"] for r in got) == ["a", "new"]
    assert draft_bundle.copy_src({"copy_of": "own/Hall"}, own) == own


# ---------- seeing past trees (canopy.py) ----------
def test_canopy_names_and_how_much_a_crown_hides_from_above():
    from tools.places.look import canopy
    assert canopy.is_canopy({"kind": "tree", "edid": "ArgoniaTreeJungle06"})
    assert canopy.is_canopy({"kind": "static", "edid": "HistTree03"})
    assert canopy.is_canopy({"kind": "plant", "edid": "HangingMoss01"})
    assert not canopy.is_canopy({"kind": "static", "edid": "HistRootsLarge01"})
    assert not canopy.is_canopy({"kind": "building", "edid": "MurkmireHut01"})
    hut = piece("hut", [0, 0, 0], [-100, -100, 0], [100, 100, 200], kind="building", edid="MurkmireHut01")
    crown = piece("crown", [0, 0, 250], [-400, -400, 0], [400, 400, 150], kind="tree", edid="ArgoniaTreeJungle06")
    aside = piece("aside", [3000, 0, 600], [-400, -400, 0], [400, 400, 300], kind="tree", edid="ArgoniaTreeJungle06")
    cam = geom.frame([-150, -150, 0], [150, 150, 200], "s", "top", 400, 300)
    got = canopy.hidden(cam, [hut], [hut, crown])
    assert got["seen"] > 0 and got["frac"] == 1.0 and got["by"] == ["ArgoniaTreeJungle06"]
    assert canopy.hidden(cam, [hut], [hut, aside])["frac"] == 0.0
    assert canopy.cut_height(100) == 100 + canopy.HEAD


# ---------- hands (hands.py) ----------
class _Sc:
    def __init__(self, rows, pieces, ground, space="exterior"):
        self.refs = {r["id"]: r for r in rows}
        self.pieces, self.ground, self.space, self.bases = pieces, ground, space, {}


def test_a_duplicate_gets_its_own_seat_and_reason_never_the_originals():
    from tools.places.look import hands
    g = Flat(100)
    deck = {"id": "deck", "base": "B:deck", "pos": [0, 0, 300], "rot": [0, 0, 0], "seat": {"mode": "ground", "dz": 200}}
    hut = {"id": "hut", "base": "B:hut", "pos": [0, 0, 320], "rot": [0, 0, 0], "seat": {"mode": "on", "on": "deck", "dz": 20},
           "why": "the elder's house", "src": "S:1"}
    crate = {"id": "crate", "base": "B:crate", "pos": [50, 0, 320], "rot": [0, 0, 0], "seat": {"mode": "on", "on": "deck", "dz": 20},
             "why": "a crate"}
    pieces = [piece("deck", [0, 0, 300], [-200, -200, 0], [200, 200, 20]),
              piece("hut", [0, 0, 320], [-100, -100, 0], [100, 100, 200], kind="building"),
              piece("crate", [50, 0, 320], [-20, -20, 0], [20, 20, 40])]
    sc = _Sc([deck, hut, crate], pieces, g)
    # the house and its deck copied together: the house stands on the deck's copy; the deck keeps its ground rule
    got = hands.duplicate_rows(sc, [deck, hut], 1000, 0, "a second house for the new family", lambda i: f"new{i}")
    d2, h2 = got
    assert d2["seat"] == {"mode": "ground", "dz": 200} and d2["pos"][:2] == [1000, 0] and d2["pos"][2] == pytest.approx(300)
    assert h2["seat"]["on"] == "new0" and all(x["why"] == "a second house for the new family" for x in got)
    assert "src" not in h2
    # the crate copied alone, off its deck: never on the original's deck; down on the ground at its height over it
    (c2,) = hands.duplicate_rows(sc, [crate], 1000, 0, "another crate", lambda i: "c2")
    assert c2["seat"]["mode"] == "ground" and c2["seat"]["dz"] == pytest.approx(220)
    # copied along the same deck: on the deck under it
    (c3,) = hands.duplicate_rows(sc, [crate], -100, 0, "another crate", lambda i: "c3")
    assert c3["seat"] == {"mode": "on", "on": "deck", "dz": pytest.approx(20)}
    # in a room a copy keeps its height
    (c4,) = hands.duplicate_rows(_Sc([crate], pieces, g, space="Hall"), [crate], 10, 0, "x", lambda i: "c4")
    assert c4["seat"] == {"mode": "free"}



def test_a_hand_places_any_base_and_a_studio_op_as_one_stroke(tmp_path):
    import math
    from tools.places.look import verbs

    class G:
        def height(self, x, y):
            return 100.0
    sc = _Sc([], [], G())
    sc.place_id = "p"
    sess = {}
    (op,) = verbs._hand(sc, "place", ["B:rack", "10,20", "--above", "5", "--rot", "90", "--why", "fish racks"], sess)
    r = op["ref"]
    assert op["op"] == "ref.add" and r["base"] == "B:rack" and r["pos"] == [10, 20, 105] and r["seat"] == {"mode": "above", "dz": 5}
    assert r["why"] == "fish racks" and r["rot"][2] == pytest.approx(math.pi / 2, abs=1e-4)
    (op2,) = verbs._hand(sc, "place", ["B:pole", "1,2,300", "--why", "a pole"], sess)
    assert op2["ref"]["seat"]["mode"] == "free" and op2["ref"]["pos"][2] == 300 and op2["ref"]["id"] != r["id"]
    assert r["scale"] == 1 and op2["ref"]["scale"] == 1
    (op3,) = verbs._hand(sc, "place", ["B:tent", "1,2,300", "--scale", "0.56", "--why", "a tent on a small deck"], sess)
    assert op3["ref"]["scale"] == pytest.approx(0.56)
    sc.bases = {"B:smoke": {"kind": "static", "model": "effects/ambient/fxsmokelargeclose01.nif"}, "B:egg": {"kind": "static"}}
    (op4,) = verbs._hand(sc, "place", ["B:smoke", "1,2,300", "--why", "smoke over the fire"], sess)
    assert op4["ref"]["kind"] == "other"                                 # the base's own kind, not "static"
    (op5,) = verbs._hand(sc, "place", ["B:egg", "1,2,300", "--within", "p.nest", "--why", "an egg in its nest"], sess)
    assert op5["ref"]["seat"]["carrier"] == "p.nest" and op5["ref"]["kind"] == "static"
    with pytest.raises(ValueError):
        verbs._hand(sc, "place", ["B:pole", "1,2,300"], sess)          # no reason, no piece
    f = tmp_path / "op.json"
    f.write_text('[{"op": "path.add", "path": {"id": "w1", "kind": "walkway", "points": [[0, 0], [1, 1]]}}]')
    (po,) = verbs._hand(sc, "op", [str(f)], sess)
    assert po["op"] == "path.add" and po["space"] == "exterior" and po["call"] == "fault"

# ---------- sections by the mesh's outline (outline.py) ----------
def test_a_section_outlines_a_flights_treads_from_its_triangles_not_its_box():
    from tools.places.look import outline
    # a flight's two treads, level, 0..200 along x, at z 0 and 50, 100 wide; and a stringer far off the slab
    treads = np.array([[[0, -50, 0], [100, -50, 0], [100, 50, 0]], [[100, -50, 50], [200, -50, 50], [200, 50, 50]],
                       [[0, 400, 0], [200, 400, 0], [200, 400, 100]]], float)
    p = {"m": xform.matrix([1000, 0, 0], [0, 0, 0], 1.0)}
    W = outline.world_tris(p, treads)
    assert W[0, 0].tolist() == [1000, -50, 0]
    kept = outline.in_slab(W, [[900, 0], [1300, 0]], 96)
    assert len(kept) == 2                      # the stringer 400 off the line is outside the slab
    cam = geom.section_camera([900, 0], [1300, 0], -50, 150, 200, 100, 96)
    m = outline.mask(cam, kept, (200, 100))
    e = outline.edge(m)
    assert m.getbbox() is not None and e.getbbox() is not None   # edge-on treads still leave a mark
    assert outline.model_tris(None) is None


def test_the_overlay_marks_doors_and_street_points_by_the_checks_own_rule():
    """With the build check's verdicts the overlay says what the check says: a door whose navmesh the check calls an
    island is red even where its triangle lies on the largest island, and the street samples off are the check's."""
    from tools.places.look import mesh, verbs
    v, t, nb = _two_decks()
    M = mesh.Mesh(v, t, nb, doors=[(0, "door1")])
    door = piece("door1", [50, 50, 0], [-10, -10, 0], [10, 10, 100], kind="door", door={"to_space": "Hut", "arrival": [50, 50, 0]})

    class S:
        pieces = [door]
        files = {"paths": [{"id": "st1", "points": [[10, 10], [190, 10]]}]}

        class ground:
            @staticmethod
            def height(x, y):
                return 0.0
    plain = verbs.mesh_marks(S, M)
    assert plain[0][0][2] is True
    net = {"doors_off": {"door1"}, "samples": [("st1", (10, 10), True), ("st1", (74, 10), False)]}
    doors, pts = verbs.mesh_marks(S, M, net)
    assert doors[0][2] is False and [on for _, on in pts] == [True, False]


# ---------- what a capture shows (capture.py, framing.py) ----------
def _ids(rows):
    import base64
    a = np.array(rows, np.int32)[::-1]   # as WebGL reads: bottom row first
    rgba = np.stack([a & 255, (a >> 8) & 255, (a >> 16) & 255, np.full_like(a, 255)], -1).astype(np.uint8)
    return base64.b64encode(rgba.tobytes()).decode(), a.shape[1], a.shape[0]


def test_decode_reads_ids_top_row_first():
    from tools.places.look import capture
    b, w, h = _ids([[16, 17], [1, 300000]])
    assert capture.decode(b, w, h).tolist() == [[16, 17], [1, 300000]]


def test_ref_at_names_what_is_drawn_at_the_pixel():
    from tools.places.look import capture
    ids = np.array([[0, 16], [1, 2]])
    table = [["a", "static", "m.nif", 0, 0]]
    assert capture.ref_at(ids, table, 16, 1, 0)["ref"] == "a"
    assert capture.ref_at(ids, table, 16, 0, 0) == {"what": "sky"}
    assert capture.ref_at(ids, table, 16, 0, 1) == {"what": "land"}


def test_score_good_and_failed():
    from tools.places.look import capture
    table = [["s", "building", "", 0, 0], ["t", "tree", "", 0, 0]]
    ids = np.array([[16] * 4 + [1] * 6] * 10)
    good = capture.score(ids, table, 16, {"s"}, {"total": 40, "in_frame": 40}, {})
    assert good["capture"] == "good" and good["subject_seen"] == 1.0 and good["subject_fills"] == 0.4
    hid = capture.score(ids, table, 16, {"s"}, {"total": 200, "in_frame": 200}, {})
    assert hid["capture"] == "failed" and "20%" in hid["why"]
    ids2 = np.array([[17] * 8 + [16] * 2] * 10)   # a tree over most of the lens, no ground, camera inside
    bad = capture.score(ids2, table, 16, {"s"}, {"total": 20, "in_frame": 20}, {"t": {"edid": "Oak", "kind": "tree"}},
                        inside="the camera is inside a tree's crown (Oak)")
    assert bad["capture"] == "failed"
    assert "no ground is drawn" in bad["why"] and "covers 80% of the lens" in bad["why"] and "crown" in bad["why"]
    assert bad["occluders"][0] == {"piece": "t", "edid": "Oak", "kind": "tree", "share": 0.8}
    part = capture.score(ids, table, 16, {"s"}, {"total": 400, "in_frame": 40}, {}, part=True)
    assert part["capture"] == "good"


def test_camera_inside_ground_box_and_tree():
    from tools.places.look import capture
    house = piece("h", (0, 0, 0), (-100, -100, 0), (100, 100, 300), kind="building")
    tree = piece("t", (1000, 0, 0), (-200, -200, 0), (200, 200, 1000), kind="tree")
    assert "under the ground" in capture.camera_inside([500, 0, 90], [house], 100.0)
    assert "inside" in capture.camera_inside([0, 0, 112], [house], 0.0)
    assert capture.camera_inside([1150, 0, 112], [tree], 0.0) is None          # under the crown, beside the trunk
    assert "trunk" in capture.camera_inside([1000, 0, 112], [tree], 0.0)
    assert "crown" in capture.camera_inside([1150, 0, 700], [tree], 0.0)
    hist = piece("H", (1000, 0, 0), (-200, -200, 0), (200, 200, 1000), edid="HistTree01")   # a Hist placed as a static
    assert capture.camera_inside([1150, 0, 112], [hist], 0.0) is None          # on the ring under its crown
    assert "trunk" in capture.camera_inside([1000, 0, 112], [hist], 0.0)


def test_helper_kind_names_what_the_game_never_draws():
    from tools.places.look import capture
    assert capture.helper_kind({"model": "markers/markerxheading.nif", "kind": "static"}) == "heading marker"
    assert capture.helper_kind({"model": "", "edid": "XMarker", "kind": "static"}) == "x-marker"
    assert capture.helper_kind({"model": "clutter/barrel01.nif", "edid": "Barrel01", "kind": "container"}) is None


def test_candidates_and_tall():
    from tools.places.look import framing
    c = framing.candidates("n", "eye")
    assert c[0] == ("n", "eye", 1.0, False) and len(c) == len(set(c)) and ("n", "eye", 1.0, True) in c
    assert {s for s, *_ in c[:5]} == {"n", "ne", "nw", "e", "w"}
    assert framing.is_tall([0, 0, 0], [400, 400, 2000]) and not framing.is_tall([0, 0, 0], [1500, 1400, 1540])
    assert framing.base_box([0, 0, 0], [400, 400, 2000])[1][2] == 400
    far = framing.candidates("n", "eye", distance=2.0)
    assert far[0] == ("n", "eye", 2.0, False) and ("n", "eye", 3.2, False) in far


def test_stand_steps_out_of_pieces_onto_the_floor():
    from tools.places.look import framing
    floor = lambda x, y: None if x < -50 else 10.0   # noqa: E731  no floor west of x=-50
    blocked = lambda e: "inside" if 400 <= e[0] <= 600 and abs(e[1]) < 100 else None   # noqa: E731
    st = framing.stand([0, 0, 0], [1, 0], 500.0, floor, blocked)
    assert st["pos"][2] == 10.0 + geom.EYE
    assert not (400 <= st["pos"][0] <= 600 and abs(st["pos"][1]) < 100)
    assert framing.stand([0, 0, 0], [-1, 0], 500.0, lambda x, y: None, blocked) is None


# ---------- survey (survey.py) ----------
def test_survey_plan_hashes_and_changed():
    from tools.places.look import survey
    p = survey.plan()
    assert len(p) == 14 and sum(t.get("height") == "eye" for t in p) == 8 and sum(bool(t.get("section")) for t in p) == 2
    assert sum(bool(t.get("own_light")) for t in p) == 1
    refs = [{"id": "a", "cluster": "b01", "pos": [0, 0, 0]}, {"id": "b", "cluster": "b02", "pos": [1, 0, 0]}]
    h = survey.structure_hashes(refs)
    assert set(h) == {"b01", "b02", "_place"}
    assert survey.changed(h, h) == []
    moved = survey.structure_hashes([refs[0], dict(refs[1], pos=[2, 0, 0])])
    assert survey.changed(h, moved) == ["b02", "_place"]
    assert survey.changed({}, h) == ["b01", "b02", "_place"]


def test_survey_table_text_says_failed_tiles():
    from tools.places.look import survey
    rows = [{"tile": "N near", "capture": "good", "subject_seen": 0.8, "subject_fills": 0.1, "land": 0.4, "sky": 0.3,
             "occluders": [{"piece": "x", "edid": "Oak", "share": 0.05}]},
            {"tile": "S near", "capture": "failed", "why": "only 2% of the subject is seen"}]
    t = survey.table_text("b01", rows)
    assert "1 of 2 tiles failed" in t and "Oak 5%" in t and "FAILED: only 2%" in t


def test_survey_tiles_have_a_file_each():
    from tools.places.look import survey
    names = [survey.tile_file(i + 1, t) for i, t in enumerate(survey.plan())]
    assert len(set(names)) == len(names) == 14
    assert names[0] == "01-n-near.png" and names[4] == "05-n-far.png" and names[8] == "09-ne-high.png"
    assert names[10] == "11-s-top.png" and names[11] == "12-section-west-east.png" and names[13] == "14-se-lit.png"
    assert (survey.TW, survey.TH) == (1280, 960) and (survey.SW, survey.SH) == (640, 480)
    assert survey.table_text("b01", [{"tile": "N near", "capture": "good", "file": "/x/01-n-near.png"}]).count("01-n-near.png") == 1


def test_views_are_1920_wide_and_labels_scale_with_width():
    from PIL import Image, ImageDraw
    from tools.places.look import draw, verbs
    assert (verbs.draw_w(), verbs.draw_h()) == (1920, 1440)
    a, b = Image.new("RGBA", (768, 576)), Image.new("RGBA", (1920, 1440))
    ha = draw.tag(ImageDraw.Draw(a), (300, 300), "label")
    hb = draw.tag(ImageDraw.Draw(b), (800, 800), "label")
    assert abs((hb[3] - hb[1]) / (ha[3] - ha[1]) - 2.5) < 0.3
    assert abs((hb[2] - hb[0]) / (ha[2] - ha[0]) - 2.5) < 0.3


def test_ground_grid_is_off_unless_asked():
    import inspect
    from tools.places.look import draw
    assert inspect.signature(draw.annotate).parameters["grid"].default is False


def test_id_buffer_enlarged_to_the_image():
    from tools.places.look import capture
    ids = np.array([[1, 2], [3, 4]])
    big = capture.enlarge(ids, 5, 4)
    assert big.shape == (4, 5) and big[0, 0] == 1 and big[0, 4] == 2 and big[3, 0] == 3 and big[3, 4] == 4
    assert capture.enlarge(ids, 2, 2) is ids


def test_pick_scale_of_a_survey_tile():
    from tools.places.look import verbs
    assert verbs.cam_scale({"w": 1280, "sw": 640}) == 2.0 and verbs.cam_scale({"w": 1920}) == 1.0


# ---------- measure (measure.py) ----------
class _Flat:
    def __init__(self, z):
        self.z = z

    def height(self, x, y):
        return self.z


def test_measure_eaves_and_collar():
    from tools.places.look import measure
    body = piece("h", (0, 0, 100), (-200, -200, 0), (200, 200, 400), kind="building")
    e = measure.eaves(body, _Flat(100.0))
    assert e["eaves_over_ground"] == 220 and not e["flag"]   # 500 - 0.45 * 400 = 320 top-less-share, over 100
    assert measure.eaves(body, _Flat(250.0))["flag"]
    tree = piece("t", (0, 0, 20), (-50, -50, 0), (50, 50, 900), kind="tree")
    assert measure.collar(tree, _Flat(100.0)) == {"collar_over_ground": -80, "flag": True}
    assert not measure.collar(tree, _Flat(50.0))["flag"]


def test_a_house_platform_is_a_deck_steps_leave_from(monkeypatch):
    """A stilt house's own platform (a model that is no walkway, e.g. blackwood/house04platform.nif) is the deck a
    flight is laid from: its flat top at least DECK_MIN wide both ways; a narrow top or a walkway model is not."""
    from tools.places import check as C
    from tools.places.look import hands
    top = np.array([[[-400, -300, 74], [400, -300, 74], [400, 300, 74]], [[-400, -300, 74], [400, 300, 74], [-400, 300, 74]],
                    [[-10, -10, 10], [10, -10, 10], [10, 10, 10]]], dtype=float)
    monkeypatch.setattr(C, "_up_faces", lambda m, b: top)
    base = {"model": "argonia/blackwood/house04platform.nif", "bounds": [[-447, -354, -412], [441, 347, 74]]}
    assert hands.platform_top(base) == (74.0, (-400.0, -300.0, 400.0, 300.0))
    monkeypatch.setattr(C, "_up_faces", lambda m, b: top[:, :, :] * np.array([0.05, 1, 1]))
    assert hands.platform_top(base) is None                       # 40 wide: a beam, not a deck
    assert hands.platform_top({"model": "argonia/clutter/barrel.nif", "bounds": base["bounds"]}) is None


def test_the_daemon_survives_a_caller_that_left_before_its_answer():
    """A ping given up while a long call ran (or a call past its client timeout) left its socket closed: answering it
    once raised out of the daemon's loop, the daemon stopped and every call queued behind it was reset."""
    import json
    import socket as so
    from tools.places.look import daemon

    class D:
        def handle(self, req):
            return {"lines": ["x" * 400000]}
    for verb in ("_ping", "probe"):
        a, b = so.socketpair()
        b.sendall(json.dumps({"verb": verb, "place": "p", "args": []}).encode() + b"\n")
        b.close()                                    # the caller is gone
        assert daemon.answer(D(), a) is None         # no error: the daemon carries on
        a.close()
    a, b = so.socketpair()
    b.sendall(b'{"verb": "_stop", "place": "", "args": []}\n')
    assert daemon.answer(D(), a) == "stop" and b.recv(64) == b'{"ok": true}\n'


def test_a_call_reset_under_it_is_retried_once(monkeypatch):
    import tools.places.look as L
    tries = []

    def once(req, timeout):
        tries.append(req["verb"])
        if len(tries) == 1:
            raise ConnectionResetError
        return {"ok": True}
    monkeypatch.setattr(L, "_call_once", once)
    monkeypatch.setattr(L, "ensure", lambda: 0.0)
    assert L.call({"verb": "probe", "place": "p", "args": []}) == {"ok": True} and tries == ["probe", "probe"]
    tries.clear()
    monkeypatch.setattr(L, "_call_once", lambda req, t: (_ for _ in ()).throw(ConnectionResetError()))
    with pytest.raises(ConnectionResetError):
        L.call({"verb": "probe", "place": "p", "args": []})


def test_an_accepted_probe_fault_is_kept_apart_from_the_open_ones():
    """place.json draft.accepted_faults [{id, fault, why}]: the fault leaves the open list (no red outline, no count)
    and is listed as accepted with its why; a different fault of the same piece stays open."""
    from tools.places.look.scene import split_accepted
    found = [{"id": "a", "fault": "floats"}, {"id": "a", "fault": "buried"}, {"id": "b", "fault": "floats"}]
    files = {"place": {"draft": {"accepted_faults": [{"id": "a", "fault": "floats", "why": "on its roots"},
                                                     {"id": "b", "why": "any fault"}]}}}
    open_, acc = split_accepted(found, files)
    assert open_ == [{"id": "a", "fault": "buried"}]
    assert [(f["id"], f["accepted"]) for f in acc] == [("a", "on its roots"), ("b", "any fault")]
    assert split_accepted(found, None) == (found, [])


def test_at_stand_puts_the_eye_over_the_deck_under_the_point_not_the_roof_and_refuses_inside_a_mesh():
    g = Flat(0)
    deck = piece("deck", [0, 0, 300], [-200, -200, 0], [200, 200, 20])        # a stilt deck, its walk at 320
    roof = piece("roof", [0, 0, 500], [-250, -250, 0], [250, 250, 60])        # the eave over it
    door = piece("door", [0, 150, 320], [-40, -5, 0], [40, 5, 200], kind="door")
    house = piece("house", [1000, 0, 0], [-200, -200, 0], [200, 200, 800], kind="building")
    things = [deck, roof, door, house]
    assert framing.stand_surface(things, g, 0, -100) == (pytest.approx(320, abs=2), "deck")
    c = framing.stand_camera(things, g, [0, -100], *geom.aabb(door), 640, 480)
    assert c["pos"][2] == pytest.approx(320 + framing.STAND_EYE, abs=2) and c["stood"]["on"] == "deck"
    assert c["target"][1] == pytest.approx(150, abs=1)
    assert framing.stand_surface(things, g, 600, 0) == (0, None)                # off the deck: the ground
    with pytest.raises(ValueError, match="inside the mesh of"):
        framing.stand_camera(things, g, [1000, 0, 400], *geom.aabb(door), 640, 480)
    with pytest.raises(ValueError, match="inside the mesh of"):
        framing.stand_camera(things, g, [0, 0, 530], *geom.aabb(door), 640, 480)  # in the roof itself


def test_at_stand_on_a_raised_deck_stands_on_its_floor_not_on_a_beam_under_it():
    """A raised deck (its floor slab over a cross-beam, the Hist deck at Jal-Veesa): the beam's top is walked too, but
    an eye over it stands inside the deck, so the camera stands on the deck's floor."""
    g = Flat(0)
    beam = piece("beam", [0, 0, 900], [-300, -40, 0], [300, 40, 40])          # walked top at 940, the deck 1.2 m over it
    deck = piece("deck", [0, 0, 1020], [-300, -300, 0], [300, 300, 30])       # its underside at 1020, its floor at 1050
    assert framing.stand_surface([beam, deck], g, 0, 0) == (pytest.approx(1050, abs=2), "deck")
    assert framing.stand_surface([beam], g, 0, 0) == (pytest.approx(940, abs=2), "beam")


def test_a_hand_placed_base_from_the_pool_resolves_from_the_catalogue(monkeypatch):
    """`look place` of a base neither the source nor the ground holds is drawn from the catalogue's row, not a stand-in box."""
    import types

    from tools.places import draft_bundle
    from tools.places.look.scene import Scene
    row = {"key": "BM:tent", "edid": "Tent", "model": "architecture/tents/smallnordictent01a.nif", "kind": "building",
           "bounds": [[-133, -131, -20], [129, 137, 161]]}
    monkeypatch.setattr(draft_bundle, "catalogue", lambda: {"BM:tent": row})
    fake = types.SimpleNamespace(bases={}, bounds_of=lambda b: (b["bounds"], True))
    p = Scene.piece(fake, {"id": "p.LOOK001PLACE", "base": "BM:tent", "pos": [0, 0, 0]})
    assert p["resolved"] and p["model"] == row["model"] and fake.bases["BM:tent"] is row
    q = Scene.piece(fake, {"id": "p.LOOK002PLACE", "base": "nowhere", "pos": [0, 0, 0]})
    assert q["missing"] and not q["resolved"]


def test_the_newer_build_s_mesh_wins_not_the_newer_export(tmp_path, monkeypatch):
    """An old shared build's mesh exported again (a new file time) never outranks a fresh draft-check build."""
    import os
    from tools.places import navexport
    from tools.places.look import mesh
    old, new = tmp_path, tmp_path / "draft_check" / "p"
    for o, t_plan, t_nav in ((old, 100, 900), (new, 500, 600)):
        (o / "shards" / "p").mkdir(parents=True, exist_ok=True)
        (o / "nav").mkdir(parents=True, exist_ok=True)
        for f, t in ((o / "shards" / "p" / "plan.json", t_plan), (o / "nav" / "p.json", t_nav)):
            f.write_text("{}")
            os.utime(f, (t, t))
    monkeypatch.setattr(navexport, "current", lambda place, o: o / "nav" / f"{place}.json")
    assert mesh.find("p", tmp_path) == (new / "nav" / "p.json", new)


def test_the_gap_between_islands_finds_the_nearest_pair_without_weighing_every_pair():
    """A long thin island and a small one above its middle: the break is where they come nearest, found by the
    kd-tree (an island's edge of a million points against another never makes every pair at once)."""
    from tools.places.look import mesh
    V = [[0, 0, 0], [1000, 0, 0], [0, 10, 0], [495, 60, 0], [505, 60, 0], [500, 200, 0]]
    M = mesh.Mesh(V, [[0, 1, 2], [3, 4, 5]], [[-1, -1, -1], [-1, -1, -1]])
    g = M.gap(int(M.lab[0]), int(M.lab[1]))
    assert g["kind"] == "missing strip" and 50 <= g["across"] <= 60 and abs(g["at"][0] - 500) <= 12


def test_a_town_s_section_is_its_middle_at_a_readable_scale_and_its_subject_what_it_cuts(monkeypatch):
    """A survey section across a whole town (16 km) is cut to its middle SECTION_SPAN, so a house is wider than a
    hair; a structure's section keeps its whole length."""
    from tools.places.look import survey, verbs
    got = []
    monkeypatch.setattr(verbs, "section_setup", lambda sc, A, B, slab, w, h: (got.append((A, B)) or {}, [], []))
    survey._cam(None, "p", {"lo": [0, 0, 0], "hi": [16000, 8000, 500]}, {"section": "west-east"}, 0.0)
    (A, B), = got
    assert abs((B[0] - A[0]) - survey.SECTION_SPAN) < 1 and A[1] == B[1] == 4000 and abs((A[0] + B[0]) / 2 - 8000) < 1
    got.clear()
    survey._cam(None, "p", {"lo": [0, 0, 0], "hi": [1200, 800, 500]}, {"section": "south-north"}, 0.0)
    (A, B), = got
    assert A == [600.0, -300] and B == [600.0, 1100]
    # a section that draws what it cuts is good though a tree fills more of it; one that draws nothing fails
    assert survey.section_verdict({"capture": "failed", "subject_seen": 0.36, "why": "a tree fills more"})["capture"] == "good"
    assert survey.section_verdict({"capture": "failed", "subject_seen": 0.0, "why": "not drawn"})["capture"] == "failed"
