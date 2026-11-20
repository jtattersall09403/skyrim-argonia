"""The playwalk's pure parts (tools/places/look/playwalk.py): the shortest walk over a fixture mesh with a stair, a
bridge and a break; station placement at the stair, the bridge and the doorway; nudges; dedup; the failure
classifier; and which rooms count as changed and what their stations are."""
import numpy as np

from tools.places.look import playwalk as pw
from tools.places.look.mesh import Mesh


def strip_mesh(profile, width=128.0, step=64.0, gap_after=None):
    """A strip of quads along +x, heights by profile(x); a missing quad after x=gap_after (a break)."""
    xs = np.arange(0, 64 * step + 1, step)
    V, T = [], []
    for x in xs:
        V += [[x, -width / 2, profile(x)], [x, width / 2, profile(x)]]
    for i in range(len(xs) - 1):
        if gap_after is not None and xs[i] == gap_after:
            continue
        a, b, c, d = 2 * i, 2 * i + 1, 2 * i + 2, 2 * i + 3
        T += [[a, c, b], [b, c, d]]
    T = np.asarray(T)
    nb = pw._neighbours(T, np.asarray(V, float), weld=1.0)
    return Mesh(V, T.tolist(), nb.tolist())


class Ground:
    """Flat ground at 0, water at `water` between x0 and x1."""
    def __init__(self, water=None, x0=0, x1=0):
        self.w, self.x0, self.x1 = water, x0, x1

    def height(self, x, y):
        return 0.0 if not (self.x0 <= x <= self.x1) else -200.0

    def water(self, x, y):
        return self.w if self.x0 <= x <= self.x1 else None


def profile(x):
    """Flat to 1024, a stair up 192 over 256, a deck at 192 (a bridge over water 1600 to 2400), down at 3200."""
    if x < 1024:
        return 0.0
    if x < 1280:
        return (x - 1024) * 0.75
    if x < 3200:
        return 192.0
    return max(0.0, 192.0 - (x - 3200) * 0.75)


def walk_of(M, a, b):
    r = pw.plan_route(M, "t", {"name": "a", "pos": a}, {"name": "b", "pos": b})
    return r


def test_route_follows_the_stair_and_bridge():
    M = strip_mesh(profile)
    r = walk_of(M, [32, 0, 0], [3000, 0, 192])
    assert "broken" not in r
    P = r["walk"]
    assert abs(P[-1, 3] - 2968) < 40
    assert P[:, 2].max() > 180     # it climbed the stair
    evs = pw.events(P, Ground(water=-100, x0=1600, x1=2400))
    whats = [w for _, w in evs]
    assert "stair foot" in whats and "stair head" in whats
    assert any(w.startswith("bridge") or w.startswith("walkway") for w in whats)
    foot = next(s for s, w in evs if w == "stair foot")
    assert 900 < foot < 1150


def test_stations_stride_events_and_doorway():
    M = strip_mesh(profile)
    r = walk_of(M, [32, 0, 0], [3000, 0, 192])
    P = r["walk"]
    evs = pw.events(P, Ground(water=-100, x0=1600, x1=2400))
    sts = pw.stations(P, evs, 256, "doorway of Hut", "end")
    assert sts[0]["what"] == "doorway of Hut" and sts[-1]["what"].startswith("end")
    gaps = np.diff([s["s"] for s in sts])
    assert gaps.max() <= 256 + pw.EVENT_MERGE + 1   # a stride station gives way to an event near it
    st = next(s for s in sts if "stair foot" in s["what"])
    assert len(pw.looks_of(st)) == 8          # the diagonals at a stair
    plain = next(s for s in sts if s["what"] == "stride")
    assert len(pw.looks_of(plain)) == 6
    assert sts[0]["dir"][0] > 0.9             # heading along the walk


def test_a_break_is_walked_to_and_named():
    M = strip_mesh(profile, gap_after=2048)
    r = walk_of(M, [32, 0, 0], [3000, 0, 192])
    assert "broken" in r and "cannot be walked to" in r["broken"]["why"]
    assert abs(r["walk"][-1, 0] - 2048) < 80   # walked to the break


def test_camera_heading_and_fov():
    st = {"pos": [0, 0, 0], "dir": [1, 0], "what": "stride", "heading": 90}
    c = pw.cam_of(st, ("left", 90, 0), 384, 288)
    assert c["pos"][2] == 112 and c["target"][1] > 900 and abs(c["target"][0]) < 1
    c = pw.cam_of(st, ("down", 0, -20), 384, 288)
    assert c["target"][2] < c["pos"][2]
    assert abs(pw.fov_v(4, 3) - 64.0) < 1


def test_nudges_stay_on_the_mesh():
    M = strip_mesh(profile)
    P = walk_of(M, [32, 0, 0], [3000, 0, 192])["walk"]
    st = {"s": 500, "pos": [500, 0, 0], "dir": [1, 0]}
    ns = pw.nudges(M, P, st)
    assert len(ns) >= 8
    for q in ns:
        assert M.tri_at(q[0], q[1], q[2])[0] >= 0


def test_dedup_marks_a_second_pass():
    st = lambda n, x: {"n": n, "s": x, "pos": [x, 0, 0], "dir": [1, 0], "heading": 90, "what": "stride"}  # noqa: E731
    a = {"name": "a", "stations": [st(1, 0) | {"what": "start"}] + [st(k, 256 * k) for k in range(1, 6)]}
    b = {"name": "b", "stations": [st(1, 0) | {"what": "start"}] + [st(k, 256 * k + 10) for k in range(1, 6)]}
    pw.dedup([a, b])
    assert not any("seen" in s for s in a["stations"])
    assert all(s["seen"][0] == "a" for s in b["stations"][1:])
    assert b["same_as"] == ["a"]


def test_classifier_capture_or_place():
    c = pw.classify
    assert c("ahead", "stride", {"inside": "the camera is inside X", "land": 0.5})["fault"] == "capture"
    assert c("ahead", "stride", {"all_inside": "WallX (building)", "land": 0.5})["fault"] == "place"
    near = {"edid": "Wall", "kind": "building", "share": 0.8, "dist": 40}
    assert c("ahead", "doorway of Hut", {"near": near, "land": 0.1})["fault"] == "place"
    assert c("left", "doorway of Hut", {"near": near, "land": 0.1})["fault"] == "capture"
    assert c("ahead", "stride", {"near": near | {"dist": 400}, "land": 0.1})["verdict"] == "good"
    assert c("down", "bridge middle", {"floor_below": 0.05, "land": 0.6})["fault"] == "place"
    assert c("ahead", "stride", {"land": 0, "water": 0, "pieces": 0.5})["fault"] == "capture"
    assert c("up", "stride", {"land": 0, "water": 0, "pieces": 0.5})["verdict"] == "good"
    assert c("ahead", "way in", {"void": 0.2}, inside=True)["fault"] == "place"
    assert c("ahead", "way in", {"all_inside": "Beam", "low_ceiling": True}, inside=True)["why"].startswith("the ceiling")


def test_room_kind():
    door = {"id": "d", "kind": "door", "base": "B", "pos": [0, 0, 0], "src": "S:1", "door": {}}
    assert pw.room_kind({"copy_of": "x/y"}, [door], [], [], "R")["kind"] == "unchanged"
    k = pw.room_kind({"copy_of": "x/y", "cut": {"box": [0, 0, 10, 10]}}, [door], [], [], "R")
    assert k["kind"] == "changed" and k["cut"] == [0, 0, 10, 10]
    k = pw.room_kind({}, [door, {"id": "a", "kind": "furniture", "base": "B", "pos": [5, 5, 0], "edid": "Bench"}], [], [], "R")
    assert k["kind"] == "changed" and k["things"][0]["name"] == "added Bench"
    assert pw.room_kind({}, [{"id": "s", "src": "S:2", "removed": True}], [], [], "R")["kind"] == "changed"
    k = pw.room_kind({}, [], [{"space": "R", "pos": [1, 2, 3], "ref": "npc.x"}], [], "R")
    assert k["kind"] == "changed" and k["spots"]
    assert pw.room_kind({}, [], [], [{"name": "P", "work": {"space": "R", "pos": [1, 2]}}], "R")["kind"] == "changed"
    assert pw.room_kind({}, [], [], [{"name": "P", "work": {"space": "exterior", "pos": [1, 2]}}], "R")["kind"] == "unchanged"


def test_room_plan_entering_and_changed():
    M = strip_mesh(lambda x: 0.0)
    door = {"id": "d", "kind": "door", "m": [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]], "door": {"to_space": "exterior"}}
    un = pw.room_plan(M, {"kind": "unchanged", "things": [], "spots": [], "cut": None}, [door])
    assert [r["name"] for r in un] == ["entering"]
    st = un[0]["stations"][0]
    assert [x[0] for x in pw.looks_of(st)] == ["ahead", "left", "right"] and st["dir"][0] > 0.9
    bench = {"id": "b", "kind": "furniture", "edid": "Bench", "model": "m/bench.nif"}
    lamp = {"id": "l", "kind": "light", "edid": "Lamp", "model": "m/lamp.nif"}
    ch = pw.room_plan(M, {"kind": "changed", "things": [{"name": "added b", "pos": [2000, 0, 0], "id": "b"},
                                                         {"name": "added l", "pos": [900, 0, 0], "id": "l"}],
                          "spots": [], "cut": [0, -64, 4096, 64]}, [door, bench, lamp])
    assert len(ch) == 3 and ch[1]["to"] == "added Bench"   # the lamp is not walked to
    assert [x[0] for x in pw.looks_of(ch[1]["stations"][0])] == ["ahead", "down", "left", "right"]
    assert ch[2]["name"] == "cut" and len(ch[2]["stations"]) == 4


def test_inside_a_box_is_a_fault_only_when_the_picture_agrees():
    why = "the camera is inside MurkmirePlatformBase01 (building, x.1)"
    assert pw.in_piece(why) == "MurkmirePlatformBase01"
    assert pw.in_piece("the camera is inside a tree's trunk (TreeX)") == "TreeX"
    air = {"all_inside": "MurkmirePlatformBase01", "in_piece": "MurkmirePlatformBase01", "land": 0.4,
           "fills": [{"edid": "land", "share": 0.4}, {"edid": "MurkmirePlatformBase01", "share": 0.3}]}
    assert pw.classify("ahead", "stride", air)["verdict"] == "good"     # under a deck on stilts: air
    solid = air | {"fills": [{"edid": "MurkmirePlatformBase01", "share": 0.9}]}
    assert pw.classify("ahead", "stride", solid)["fault"] == "place"


def test_a_deck_overhead_is_not_a_fault_looking_up():
    over = {"all_inside": "Deck", "in_piece": "Deck", "fills": [{"edid": "Deck", "share": 0.8}], "land": 0.1}
    assert pw.classify("up", "stride", over)["verdict"] == "good"


def test_a_roof_at_head_height_and_a_trunk_beside():
    roof = {"edid": "ThatchHouse", "kind": "building", "share": 0.8, "dist": 43, "top_over_eye": 60}
    v = pw.classify("right", "stride", {"near": roof, "land": 0.1})
    assert v["fault"] == "place" and "eaves" in v["why"]
    tall = roof | {"top_over_eye": 400}
    assert pw.classify("right", "stride", {"near": tall, "land": 0.1})["fault"] == "capture"
    trunk = {"all_inside": "TreeX", "in_piece": "TreeX", "fills": [{"edid": "TreeX", "share": 0.9}], "land": 0.1}
    assert pw.classify("left", "stride", trunk)["fault"] == "capture"      # standing beside it
    assert pw.classify("ahead", "stride", trunk)["fault"] == "place"       # walking into it
