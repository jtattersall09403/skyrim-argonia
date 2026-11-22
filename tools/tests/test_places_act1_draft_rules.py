"""The Act I draft rules (#80): a couple's shared bed owned by their household, a taken-out thing's links dropped, the
sap pool and its Hist accepted together by the overlap rule, a source room's partial navmesh meshed again, a place's
source plugin found with its assets, streets fording no deeper than the knee, two laid decks at one crossing made
one, a sleeper with no bed given a free one, and the work hours at the work stop."""
import json

import numpy as np

from tools.places import build as B
from tools.places import check as C
from tools.places import people
from tools.places.draft import people as dpeople
from tools.places.draft import walk
from tools.places.stock import plan as stockplan
from tools.tests.test_places_people import Ids, facts

P = "ArgoniaNWPlaces.esp"


def test_a_couples_shared_bed_is_owned_by_their_household_and_each_is_in_it():
    bed = {"id": "t.bed", "fk": f"{P}:000F00", "space": "house", "kind": "furniture", "pos": [0.0, 0.0, 0.0]}
    folk = [{"id": f"t.{w}", "base_from": "Skyrim.esm:000001", "role": "resident", "household": {"id": "t.hh"},
             "bed": {"space": "house", "ref": "t.bed"},
             "routine": [{"start": 0, "hours": 24, "kind": "sleep", "at": {"space": "house", "pos": [0, 0, 0]}}]}
            for w in ("a", "b")]
    B.PROBLEMS.clear()
    out = people.plan({"place": {"place_id": "t"}, "people": folk}, {"refs": [bed], "by_id": {"t.bed": bed}}, Ids(),
                      facts(), [])
    hh = [f for f in out["factions"] if f["edid"].startswith("ANP_t_Household")]
    assert len(hh) == 1 and bed["owner"] == hh[0]["fk"]
    assert all(any(f["faction"] == hh[0]["fk"] for f in n["factions"]) for n in out["npcs"])
    assert len(out["owned_beds"]) == 1


def test_a_lone_sleepers_bed_is_their_own():
    bed = {"id": "t.bed", "fk": f"{P}:000F00", "space": "house", "kind": "furniture", "pos": [0.0, 0.0, 0.0]}
    one = {"id": "t.a", "base_from": "Skyrim.esm:000001", "role": "resident", "bed": {"space": "house", "ref": "t.bed"},
           "routine": [{"start": 0, "hours": 24, "kind": "sleep", "at": {"space": "house", "pos": [0, 0, 0]}}]}
    B.PROBLEMS.clear()
    out = people.plan({"place": {"place_id": "t"}, "people": [one]}, {"refs": [bed], "by_id": {"t.bed": bed}}, Ids(),
                      facts(), [])
    assert bed["owner"] == out["npcs"][0]["fk"]


def test_a_thing_taken_out_takes_its_links_and_enable_parent_with_it():
    refs = [{"id": "trigger", "linked": [{"ref": "K:1", "keyword": ""}, {"ref": "K:2", "keyword": "kw"}],
             "enable_parent": "K:1", "enable_parent_flags": 0}]
    stockplan.unlink(refs, {"K:1"})
    assert refs[0]["linked"] == [{"ref": "K:2", "keyword": "kw"}] and "enable_parent" not in refs[0]


def test_a_sap_pool_and_its_hist_stand_in_each_other_by_design():
    box = [-100, -100, 0, 100, 100, 300]
    hist = {"id": "p.H1", "kind": "static", "space": "exterior", "pos": [0.0, 0.0, 0.0], "rot": [0, 0, 0], "bounds": box}
    pool = {"id": "p.sap.H1", "kind": "activator", "space": "exterior", "pos": [10.0, 0.0, 0.0], "rot": [0, 0, 0],
            "bounds": box}
    other = {**pool, "id": "p.sap.H2"}
    assert C.overlap_pairs([hist, pool]) == []
    assert C.overlap_pairs([hist, other])


def test_a_hand_placed_sap_pool_on_the_trunk_is_the_trees_own():
    from tools.places.draft import sap
    box = [-100, -100, 0, 100, 100, 300]
    hist = {"id": "p.H1", "kind": "static", "space": "exterior", "pos": [0.0, 0.0, 0.0], "rot": [0, 0, 0], "bounds": box}
    pool = {"id": "p.STOP", "base": sap.POOL, "kind": "activator", "space": "exterior", "rot": [0, 0, 0], "scale": 1.0,
            "bounds": box, "pos": [-sap.POOL_CENTRE[0], -sap.POOL_CENTRE[1], 0.0]}
    assert C.overlap_pairs([hist, pool]) == []
    assert C.overlap_pairs([hist, {**pool, "base": "K:puddle"}])


def test_eggs_lie_in_a_sap_pool_and_in_their_nest():
    """A pool of Hist sap is water: an egg laid in its shallow edge stands in it as in any water; eggs set `on` their
    nest rest on it, and two eggs on one nest rest together (King of the Murkmire's clutches at Seekhat Yol's Hist)."""
    from tools.places.draft import sap
    box = [-200, -200, -10, 200, 200, 10]
    pool = {"id": "p.sap.H1", "base": sap.POOL, "kind": "activator", "space": "exterior", "pos": [0.0, 0.0, 0.0],
            "rot": [0, 0, 0], "bounds": box}
    egg = {"id": "p.EGG", "base": "K:egg", "kind": "static", "space": "exterior", "pos": [20.0, 0.0, 0.0], "rot": [0, 0, 0],
           "bounds": [-12, -15, -12, 12, 16, 12]}
    assert C.overlap_pairs([egg, pool]) == []
    nest = {"id": "p.NEST", "base": "K:nest", "kind": "static", "space": "exterior", "pos": [500.0, 0.0, 0.0],
            "rot": [0, 0, 0], "bounds": [-40, -40, -20, 40, 40, 20]}
    on = {"mode": "on", "on": "p.NEST", "dz": 7.0}
    e1 = {**egg, "id": "p.E1", "pos": [500.0, 0.0, 7.0], "seat": on}
    e2 = {**egg, "id": "p.E2", "pos": [505.0, 3.0, 7.0], "seat": on}
    assert C.overlap_pairs([nest, e1, e2]) == []
    assert C.overlap_pairs([nest, {**e1, "seat": None}])


def test_a_source_mesh_that_misses_a_bed_or_an_arrival_is_not_kept():
    tris = np.zeros(2, [("v", "<i4", 3)])
    tris["v"] = [[0, 1, 2], [0, 2, 3]]
    mesh = {"m": {"verts": np.array([[0, 0, 0], [200, 0, 0], [200, 200, 0], [0, 200, 0]], float), "tris": tris}}
    assert B.uncovered(mesh, [[100, 100, 10], [250, 100, 0]]) == 0       # under it, and within reach of its edge
    assert B.uncovered(mesh, [[100, 100, 300], [800, 100, 0]]) == 2      # a floor up, a room away
    S = {"refs": [{"fk": "d", "space": "exterior", "teleport": {"to": "d2", "pos": [1, 2, 3]}},
                  {"fk": "d2", "space": "room", "kind": "door", "pos": [0, 0, 0]},
                  {"fk": "b", "space": "room", "kind": "furniture", "pos": [5, 5, 5]},
                  {"fk": "c", "space": "room", "kind": "clutter", "pos": [9, 9, 9]}]}
    assert B.room_stands({"space": "room"}, S) == [[1.0, 2.0, 3.0], [5.0, 5.0, 5.0]]


def test_a_place_source_plugin_is_found_with_its_assets(tmp_path, monkeypatch):
    from tools.navmesh import meshes
    data = tmp_path / "game" / "Data"
    data.mkdir(parents=True)
    (tmp_path / "game" / "newworld-assets" / "mod").mkdir(parents=True)
    (tmp_path / "game" / "newworld-assets" / "mod" / "Mod.esp").write_bytes(b"TES4")
    assert meshes.plugin_file("Mod.esp", data, stack=tmp_path / "none") == tmp_path / "game" / "newworld-assets" / "mod" / "Mod.esp"
    assert meshes.plugin_file("Other.esp", data, stack=tmp_path / "none") is None


def test_two_laid_decks_at_one_crossing_are_one():
    bases = {"D": {"bounds": [[-128, -64, 0], [128, 64, 100]]}}
    rows = [{"id": "p.a", "base": "D", "kind": "building", "pos": [0, 0, 0], "rot": [0, 0, 0], "src": None,
             "why": "carries street 01 over our water"},
            {"id": "p.b", "base": "D", "kind": "building", "pos": [30, 10, 0], "rot": [0, 0, 0.3], "src": None,
             "why": "carries street 02 over our water"},
            {"id": "p.c", "base": "D", "kind": "building", "pos": [600, 0, 0], "rot": [0, 0, 0], "src": None,
             "why": "carries street 02 over our water"}]
    rows.append({**rows[1], "id": "p.d", "pos": [10, 5, 30], "seat": {"on": "p.a"}})   # a join's next piece, resting on it
    assert walk.twins(rows, bases, log=lambda *_: None) == 1
    assert [r["id"] for r in rows] == ["p.a", "p.c", "p.d"]


def test_a_sleeper_with_no_bed_takes_a_free_camp_bed(tmp_path, monkeypatch):
    from tools.places.draft import interiors
    from tools.tests.test_places_draft_walk import _Nav, _Src
    p = tmp_path / "p"
    (p / "spaces" / "exterior").mkdir(parents=True)
    walk.io.write_jsonl(p / "spaces" / "exterior" / "refs.jsonl",
                        [{"id": "roll", "base": "R", "kind": "furniture", "pos": [50, 50, 0]}])
    walk.io.write_jsonl(p / "people.jsonl", [
        {"id": "m", "role": "merchant", "bed": None, "home": None,
         "routine": [{"kind": "sleep", "at": {"space": "exterior", "pos": [9, 9]}}, {"kind": "work", "at": {}}]}])
    monkeypatch.setattr(interiors, "is_bed", lambda b: True)
    navs = {"main": _Nav("main", [(0, 0), (1, 0), (0, 1), (1, 1)])}
    W = walk.Walkable({"navs": navs}, comp=C.components(navs, {}))
    assert walk.rehome("p", W, {"R": {}}, _Src([]), p, log=lambda *_: None) == 1
    m = walk.io.read_jsonl(p / "people.jsonl")[0]
    assert m["bed"] == {"space": "exterior", "ref": "roll", "radius": 128} and m["routine"][0]["at"] == m["bed"]


def test_the_work_hours_are_spent_at_the_work_stop():
    folk = [{"id": "a", "work": {"space": "room", "pos": [1, 2, 3], "radius": 512},
             "routine": [{"kind": "sleep", "at": {"space": "room"}}, {"kind": "work", "at": {"space": "room", "pos": [1, 2]}}]}]
    assert dpeople.work_stops(folk) == ["a"]
    assert folk[0]["routine"][1]["at"] == {"space": "room", "pos": [1, 2, 3], "radius": 512}
    assert dpeople.work_stops(folk) == [] and json.dumps(folk)


def test_a_stop_at_a_point_under_a_deck_stands_on_the_network():
    """An eat stop at a plan point the build would seat on mud under a landing's deck (an island of the mesh) is
    moved onto the network at the deck's height; a stop already on the network where the build seats it stays."""
    class W:
        zref = staticmethod(lambda x, y: 0.0)

        def on(self, p, tol=None):
            return len(p) == 3 and (p[2] > 100 or p[0] > 500)   # the deck at z 150, the ground east of x 500

        def snap(self, p, reach):
            return tuple(p[:2])

        def stood(self, q):
            return [round(float(q[0]), 1), round(float(q[1]), 1), 150.0]
    folk = [{"id": "o", "routine": [{"kind": "eat", "at": {"space": "exterior", "pos": [10, 20]}},
                                    {"kind": "wander", "at": {"space": "exterior", "pos": [600, 20]}},
                                    {"kind": "sleep", "at": {"space": "exterior", "ref": "bed"}}]}]
    assert walk.stand_stops("p", folk, W(), log=lambda *_: None) == 1
    r = folk[0]["routine"]
    assert r[0]["at"]["pos"] == [10.0, 20.0, 150.0] and r[1]["at"]["pos"] == [600, 20]
    assert r[2]["at"] == {"space": "exterior", "ref": "bed"}


def test_a_door_and_its_own_frame_stand_in_each_other_by_design():
    door = {"id": "p.D", "kind": "door", "space": "exterior", "pos": [0.0, 0.0, 0.0], "rot": [0, 0, 0],
            "bounds": [-80, -20, 0, 80, 20, 250]}
    pillar = {"id": "p.P", "kind": "building", "edid": "XanmeerExtWallPillar01", "space": "exterior",
              "pos": [30.0, 0.0, 0.0], "rot": [0, 0, 0], "bounds": [-40, -40, 0, 40, 40, 600]}
    wall = {"id": "p.W", "kind": "building", "edid": "Hut01", "space": "exterior", "pos": [0.0, 180.0, 0.0],
            "rot": [0, 0, 0], "bounds": [-200, -200, 0, 200, 200, 400]}    # the door in its wall ring
    crate = {**door, "id": "p.C", "kind": "container"}
    assert C.overlap_pairs([door, pillar]) == []
    assert C.overlap_pairs([door, wall]) == []
    assert C.overlap_pairs([door, {**wall, "pos": [0.0, 0.0, 0.0]}])     # a door in a house's middle still faults
    assert C.overlap_pairs([crate, pillar])
