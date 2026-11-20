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
    assert res["left_for_owner"] == [{"stroke": 3, "owner_rows": [c["id"]]}]
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
