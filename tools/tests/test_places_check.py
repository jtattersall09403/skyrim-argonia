"""tools/places/check.py: a small synthetic place passes every check, and one broken fixture per check fails it.

The fixture is made here (no game data): one exterior cell with flat ground at z 800, a hut, a door paired with an
interior door, one person with an owned bed and two stops, one navmesh per space, a cleared plant, a path."""
import base64
import copy

import numpy as np
import pytest

from tools.navmesh import nvnm
from tools.places import check as C

W = "ArgoniaNewWorld.esm"
P = "ArgoniaNWPlaces.esp"
CELL = (0, 0)
FLAT = 100  # steps (800 units)


def k(n, f=P):
    return f"{f}:{n:06X}"


def nav(fk, space, cell, x0, y0, x1, y1, z, doors=()):
    verts = np.array([[x0, y0, z], [x1, y0, z], [x1, y1, z], [x0, y1, z]], np.float32)
    tris = np.zeros(2, nvnm.TRI)
    tris[0] = ((0, 1, 2), (-1, -1, 1), nvnm.FOUND, 0)
    tris[1] = ((0, 2, 3), (0, -1, -1), nvnm.FOUND, 0)
    n = nvnm.Nvnm(1 if space == "exterior" else 0, cell, None if space == "exterior" else 1, verts, tris)
    n.doors = np.array([(t, nvnm.PATHING_DOOR, 0) for t, _ in doors], nvnm.DOOR_TRI) if doors else np.zeros(0, nvnm.DOOR_TRI)
    out = C.Nav(fk, space, cell, n, lambda r: "")
    out.doors = list(doors)
    return out


def land_cell(x, y, steps=FLAT):
    d = np.zeros((33, 33), np.int8)
    return {"x": x, "y": y, "fk": k(0x100, W), "land": k(0x101, W), "offset": float(steps),
            "deltas": base64.b64encode(d.tobytes()).decode(), "refs": [
                {"fk": k(0x500, W), "base": k(0x10, W), "base_type": "TREE", "pos": [3000.0, 3000.0, 800.0], "flags": 0},
                {"fk": k(0x501, W), "base": k(0x10, W), "base_type": "TREE", "pos": [1000.0, 3500.0, 800.0], "flags": 0}]}


def ctx():
    hut = {"fk": k(1), "id": "t.hut", "kind": "building", "space": "exterior", "pos": [2000.0, 2000.0, 800.0], "rot": [0, 0, 0],
           "seat": {"mode": "ground", "dz": 0}}
    door = {"fk": k(2), "id": "t.door", "kind": "door", "space": "exterior", "pos": [2000.0, 1700.0, 800.0], "rot": [0, 0, 0],
            "seat": {"mode": "ground", "dz": 0}}
    idoor = {"fk": k(3), "id": "t.idoor", "kind": "door", "space": "house", "pos": [100.0, 0.0, 0.0], "rot": [0, 0, 0], "src": "X.esm:000001"}
    bed = {"fk": k(4), "id": "t.bed", "kind": "furniture", "space": "house", "pos": [300.0, 300.0, 0.0], "rot": [0, 0, 0]}
    work = {"fk": k(5), "id": "t.work", "kind": "marker", "space": "exterior", "pos": [2500.0, 1500.0, 800.0], "rot": [0, 0, 0],
            "seat": {"mode": "ground", "dz": 0}}
    rent = {"fk": k(6), "id": "t.rentbed", "kind": "furniture", "space": "house", "pos": [300.0, 500.0, 0.0], "rot": [0, 0, 0]}
    plan = {"refs": [hut, door, idoor, bed, work, rent], "cells": [{"x": 0, "y": 0, "cell": k(0x100, W)}],
            "clear": [{"fk": k(0x500, W), "base": k(0x10, W), "pos": [3000.0, 3000.0, 800.0], "cell": [0, 0]}],
            "people": {"npcs": [{"fk": k(10), "id": "t.person"}], "actors": [{"fk": k(11)}], "markers": []}}

    def dref(r, **kw):
        d = {"fk": r["fk"], "base": k(0x20, "Skyrim.esm"), "base_type": "STAT", "base_edid": "SwampHut", "model": "meshes/x/hut.nif",
             "pos": r["pos"], "rot": r["rot"], "scale": 1.0, "flags": 0, "space": "exterior" if r["space"] == "exterior" else "house",
             "bounds": [-50, -50, 0, 50, 50, 100]}
        d.update(kw)
        return d
    dump = {"masters": ["Skyrim.esm", W], "unresolved": [], "levelled": [],
            "refs": [dref(hut, bounds=[-200, -200, 0, 200, 200, 400]),
                     dref(door, base_type="DOOR", base_edid="SwampDoor", persistent=True, bounds=[-40, -5, 0, 40, 5, 200],
                          door={"to_ref": k(3), "to_pos": [200.0, 0.0, 0.0], "to_rot": [0, 0, 0]}),
                     dref(idoor, base_type="DOOR", base_edid="SwampDoor", persistent=True, bounds=[-40, -5, 0, 40, 5, 200],
                          door={"to_ref": k(2), "to_pos": [2000.0, 1500.0, 800.0], "to_rot": [0, 0, 0]}),
                     dref(bed, base_type="FURN", base_edid="Bed", owner=k(10), bounds=[-50, -100, 0, 50, 100, 60]),
                     dref(work, base_type="STAT", base_edid="XMarkerHeading", bounds=None),
                     dref({"fk": k(6), "pos": [300.0, 500.0, 0.0], "rot": [0, 0, 0], "space": "house"}, base_type="FURN", base_edid="Bed",
                          owner=k(31), bounds=[-50, -100, 0, 50, 100, 60])],
            "overrides": [{"fk": k(0x500, W), "flags": 0x800}],
            "land": [], "actors": [{"fk": k(11), "base": k(10)}], "cells": [],
            "rent_voices": ["Skyrim.esm:013AEE", "Skyrim.esm:013AEF"],
            "rent_offer": [{"fn": "GetInFaction", "run_on": "Subject", "op": "EqualTo", "value": 1.0, "faction": "Skyrim.esm:09CC97"},
                           {"fn": "GetActorValue", "run_on": "Subject", "op": "EqualTo", "value": 0.0, "actor_value": "Variable09"},
                           {"fn": "GetItemCount", "run_on": "Target", "op": "GreaterThanOrEqualTo", "value": "Skyrim.esm:09CC98", "item": "Skyrim.esm:00000F"}],
            "npcs": [{"fk": k(10), "packages": [k(20), k(21)], "factions": ["ANP_t_CrimeFaction", "ANP_t_vendor", "JobMerchantFaction", "JobInnkeeperFaction", "JobRentRoomFaction"],
                      "faction_keys": [k(30), k(31), "Skyrim.esm:051596", "Skyrim.esm:05091B", "Skyrim.esm:09CC97"], "class": "",
                      "faction_ranks": [{"faction": "Skyrim.esm:09CC97", "rank": -1}, {"faction": "Skyrim.esm:05091B", "rank": 0},
                                        {"faction": "Skyrim.esm:051596", "rank": 0}],
                      "voice": "Skyrim.esm:013AEE",
                      "scripts": [{"name": "RentRoomScript", "props": [{"name": "Bed", "type": "object", "value": k(6)},
                                                                      {"name": "WI", "type": "object", "value": "Skyrim.esm:035D64"}]}]}],
            "packages": [{"fk": k(20), "edid": "sleep", "location": k(4)}, {"fk": k(21), "edid": "work", "location": k(5)}],
            "factions": [{"fk": k(30), "vendor": False}, {"fk": k(31), "vendor": True, "chest": k(40)}], "classes": []}
    navs = {k(0x600, W): nav(k(0x600, W), "exterior", (0, 0), 1000, 1000, 3500, 3500, 800, doors=[(0, k(2))]),
            k(50): nav(k(50), "house", None, -200, -200, 600, 600, 0, doors=[(0, k(3))])}
    return {"plan": plan, "dump": dump, "facts": {"cells": [land_cell(0, 0)]}, "navs": navs,
            "gives": [{"give_kind_id": "trader-general", "detail": "trader"}, {"give_kind_id": "inn-room", "detail": "a room"}],
            "land_rows": [], "paths": [{"id": "t.path", "points": [[2000.0, 1600.0], [2600.0, 1200.0]], "width": 200}]}


def test_the_good_fixture_passes_every_check():
    res = C.run(ctx())
    assert not any(res.values()), res


def broken(name):
    c = copy.deepcopy(ctx())
    d, p = c["dump"], c["plan"]
    if name == "plugin":
        d["unresolved"].append(f"{k(1)} -> Gone.esp:000001 <IStaticGetter>")
    elif name == "seat":
        d["refs"][0]["pos"] = [2000.0, 2000.0, 900.0]
    elif name == "overlap":
        d["refs"][4]["pos"] = [2010.0, 2010.0, 800.0]
        p["refs"][4]["kind"] = "static"
    elif name == "doors":
        d["refs"][2]["door"]["to_ref"] = k(99)
    elif name == "people":
        d["refs"][3]["owner"] = ""
    elif name == "navmesh":
        n = c["navs"][k(50)]
        n.flags[1] |= 1
        n.links = [(0, k(0x600, W), 0)]
        n.edge[1][0] = 0
    elif name == "streets":
        c["paths"][0]["points"][1] = [3900.0, 1200.0]     # past the navmesh's edge
    elif name == "land":
        c["land_rows"] = [{"cell": [0, 0], "verts": [[5, 5, 64.0]]}]
    elif name == "clear":
        d["overrides"][0]["flags"] = 0
    elif name == "services":
        c["gives"].append({"give_kind_id": "trainer", "detail": "Expert Alchemy"})
    elif name == "nordic":
        d["refs"][0]["model"] = "meshes/architecture/whiterun/wrhouse01.nif"
    elif name == "levelled":
        d["levelled"].append("ANP_t_person -> Skyrim.esm:09AF07 LItemMiscVendorArmor75")
    return c


@pytest.mark.parametrize("name", list(C.CHECKS))
def test_each_check_can_fail(name):
    res = C.run(broken(name))
    assert res[name], f"{name} did not fail on its broken fixture"


def test_a_plant_on_a_path_fails_clear():
    c = ctx()
    c["facts"]["cells"][0]["refs"][1]["pos"] = [2300.0, 1400.0, 800.0]
    assert C.run(c)["clear"]


def patrol_ctx(link_actor=True):
    """The person's work package patrols, the vanilla way: target = the actor's linked ref, a chain of two markers."""
    c = copy.deepcopy(ctx())
    d = c["dump"]
    m2 = {"fk": k(6), "base": k(0x21, "Skyrim.esm"), "base_type": "STAT", "base_edid": "XMarkerHeading", "model": None,
          "pos": [2600.0, 1600.0, 800.0], "rot": [0, 0, 0], "scale": 1.0, "flags": 0, "space": "exterior", "bounds": None,
          "linked": [{"ref": k(5), "keyword": ""}]}
    d["refs"][4]["linked"] = [{"ref": k(6), "keyword": ""}]
    d["refs"].append(m2)
    d["packages"][1] = {"fk": k(21), "edid": "patrol", "location": None, "target": None, "target_linked": True}
    if link_actor:
        d["actors"][0]["linked"] = [{"ref": k(5), "keyword": ""}]
    return c


def test_a_patrol_by_linked_ref_passes_and_fails_without_the_actor_link():
    assert not C.run(patrol_ctx())["people"]
    assert any("no linked ref" in x for x in C.run(patrol_ctx(link_actor=False))["people"])


@pytest.mark.parametrize("what", ["rank", "voice", "script", "bed", "wi", "job"])
def test_a_broken_rent_wiring_fails_services(what):
    c = copy.deepcopy(ctx())
    n = c["dump"]["npcs"][0]
    if what == "rank":
        n["faction_ranks"][0]["rank"] = 0
    elif what == "voice":
        n["voice"] = "Skyrim.esm:013AE6"
    elif what == "script":
        n["scripts"] = []
    elif what == "bed":
        next(r for r in c["dump"]["refs"] if r["fk"] == k(6))["owner"] = k(30)
    elif what == "wi":
        n["scripts"][0]["props"][1]["value"] = ""
    elif what == "job":
        n["faction_ranks"].pop(1)
    assert C.run(c)["services"], what


def test_rent_offer_conditions_are_decided_or_named():
    v = dict(C.rent_offer_verdicts(ctx()["dump"]["npcs"][0], ctx()["dump"]["rent_offer"]))
    assert [x.split(":")[0] for x in v.values()] == ["ok", "runtime", "runtime"]
    bare = {"fk": k(10), "faction_ranks": []}
    assert "FAIL" in C.rent_offer_verdicts(bare, ctx()["dump"]["rent_offer"])[0][1]


def shrine_ctx(what=None):
    """The good fixture plus a Hist shrine: a ref of ours on an activator of ours with TempleBlessingScript."""
    c = copy.deepcopy(ctx())
    row = {"fk": k(7), "id": "t.hist", "kind": "static", "space": "exterior", "pos": [2600.0, 2400.0, 800.0], "rot": [0, 0, 0],
           "seat": {"mode": "ground", "dz": 0}}
    c["plan"]["refs"].append(row)
    d = c["dump"]
    d["refs"].append({"fk": k(7), "base": k(0x60), "base_type": "ACTI", "base_edid": "ANP_t_Shrine_hist", "model": "meshes/x/hist.nif",
                      "pos": row["pos"], "rot": row["rot"], "scale": 1.0, "flags": 0, "space": "exterior", "bounds": [-50, -50, 0, 50, 50, 100]})
    props = [{"name": "TempleBlessing", "type": "object", "value": k(0x61)},
             {"name": "BlessingMessage", "type": "object", "value": k(0x62)},
             {"name": "AltarRemoveMsg", "type": "object", "value": "Skyrim.esm:10E4F9"}]
    d["activators"] = [{"fk": k(0x60), "edid": "ANP_t_Shrine_hist", "name": "Hist", "model": "meshes/x/hist.nif",
                        "scripts": [{"name": "TempleBlessingScript", "props": props}]}]
    d["spells"] = [{"fk": k(0x61), "edid": "ANP_t_Blessing", "name": "Blessing of the Hist", "type": "Spell", "cast": "FireAndForget", "target": "Self",
                    "effects": [{"mgef": k(0x63), "mgef_edid": "ANP_t_ResistDiseaseFFSelf", "actor_value": "ResistDisease", "magnitude": 10.0, "duration": 28800, "area": 0},
                                {"mgef": "Skyrim.esm:0FBFF5", "mgef_edid": "CureDiseaseEffect", "actor_value": "None", "magnitude": 25.0, "duration": 0, "area": 0}]}]
    d["messages"] = [{"fk": k(0x62), "edid": "ANP_t_BlessingMsg", "text": "You are blessed by the Hist."}]
    c["gives"].append({"give_kind_id": "shrine-blessing", "detail": "a blessing of the Hist"})
    if what == "no_ref":
        c["plan"]["refs"].pop()
        d["refs"].pop()
        d["activators"] = []
    elif what == "no_script":
        d["activators"][0]["scripts"] = []
    elif what == "wrong_spell":
        props[0]["value"] = "Skyrim.esm:0FB999"
    elif what == "wrong_effect":
        d["spells"][0]["effects"][0]["actor_value"] = "Block"
    elif what == "short":
        d["spells"][0]["effects"][0]["duration"] = 60
    elif what == "no_message":
        props[1]["value"] = ""
    elif what == "blank_message":
        d["messages"][0]["text"] = ""
    elif what == "no_remove":
        props[2]["value"] = ""
    return c


def test_a_shrine_with_the_vanilla_blessing_passes_services():
    assert not C.run(shrine_ctx())["services"]


@pytest.mark.parametrize("what", ["no_ref", "no_script", "wrong_spell", "wrong_effect", "short", "no_message", "blank_message", "no_remove"])
def test_a_broken_shrine_fails_services(what):
    got = C.run(shrine_ctx(what))["services"]
    assert any("shrine-blessing" in x for x in got), (what, got)
    if what == "no_ref":
        assert any("no shrine ref: the draft must add one" in x for x in got)


def boat_ctx(what=None):
    """The good fixture plus a boatman of ours in a boatman faction, with one line to Truowa (a city, 20 gold)."""
    c = copy.deepcopy(ctx())
    d = c["dump"]
    boat_f = k(0x70)
    d["factions"].append({"fk": boat_f, "edid": "ANP_t_Boatman_boater", "vendor": False})
    d["npcs"][0]["faction_keys"].append(boat_f)
    d["npcs"][0]["factions"].append("ANP_t_Boatman_boater")
    marker = k(0x67, W)
    d["world_markers"] = {marker: "ANW_MapMarker_truowa"}
    props = [{"name": "Destination", "value": marker}, {"name": "Fare", "value": 20}, {"name": "Gold001", "value": "Skyrim.esm:00000F"}]
    info = {"fk": k(0x72), "prompt": "Take me to Truowa (20 gold).", "text": ["Truowa, then."], "link_to": [],
            "conditions": [{"fn": "GetInFaction", "run_on": "Subject", "op": "EqualTo", "value": 1.0, "faction": boat_f},
                           {"fn": "GetGold", "run_on": "Target", "op": "GreaterThanOrEqualTo", "value": 20.0}],
            "scripts": [{"name": "TIF_ARG_BoatTravel", "props": props}], "fragment": {"file": "TIF_ARG_BoatTravel", "on_end": "Fragment_0"}}
    d["topics"] = [{"fk": k(0x71), "edid": "ANP_t_Boat_Truowa", "name": info["prompt"], "quest": k(0x73), "branch": k(0x74), "infos": [info]}]
    c["places"] = [{"id": "truowa", "name": "Truowa", "place_kind_id": "city"}, {"id": "korydon", "name": "Korydon", "place_kind_id": "town"}]
    c["gives"].append({"give_kind_id": "carriage-or-boat", "detail": "raft-boatman to Truowa"})
    if what == "no_destination":
        c["gives"][-1]["detail"] = "raft-boatman to Truowa and Korydon"
    elif what == "no_script":
        info["scripts"] = []
    elif what == "fare_0":
        props[1]["value"] = 0
        info["conditions"][1]["value"] = 0.0
    elif what == "no_gold_condition":
        info["conditions"].pop()
    elif what == "no_faction_condition":
        info["conditions"].pop(0)
    elif what == "wrong_marker":
        d["world_markers"][marker] = "ANW_MapMarker_julo"
    elif what == "no_fragment":
        info["fragment"] = None
    elif what == "no_boatman":
        d["npcs"][0]["faction_keys"].remove(boat_f)
    return c


def test_a_boatman_with_a_line_per_destination_passes_services():
    assert not C.run(boat_ctx())["services"]


@pytest.mark.parametrize("what", ["no_destination", "no_script", "fare_0", "no_gold_condition", "no_faction_condition", "wrong_marker",
                                  "no_fragment", "no_boatman"])
def test_a_broken_boatman_fails_services(what):
    got = C.run(boat_ctx(what))["services"]
    assert any("carriage-or-boat" in x for x in got), (what, got)


def test_boat_destinations_are_read_from_the_give_detail():
    from tools.places import build as B
    assert B.boat_destinations("raft-boatman to Truowa, Korydon, Marzai and Julo") == ["Truowa", "Korydon", "Marzai", "Julo"]
    assert B.boat_destinations("fishing boat across to Soulrest") == ["Soulrest"]
    assert B.boat_destinations("a raft") == []


def seam_pair(other_y0, other_z):
    """Our cell (0,0) reaching its east line, and the world's cell (1,0) beside it from other_y0 up."""
    c = ctx()
    c["navs"] = {k(0x601): nav(k(0x601), "exterior", (0, 0), 0, 0, 4096, 4096, 800)}
    w = nav(k(0x602, W), "exterior", (1, 0), 4096, other_y0, 8192, 4096, other_z)
    w.world = True
    c["navs"][k(0x602, W)] = w
    return c


def test_an_open_seam_edge_with_ground_across_fails_navmesh():
    assert any("open seam edge" in f for f in C.check_navmesh(seam_pair(0, 820)))


def test_a_seam_with_a_step_or_only_a_corner_across_is_a_boundary():
    assert not any("open seam edge" in f for f in C.check_navmesh(seam_pair(0, 1200)))  # a step: no walk across
    assert not any("open seam edge" in f for f in C.check_navmesh(seam_pair(4096, 800)))  # touches the line at a corner


def test_a_patrol_marker_off_the_mesh_or_on_another_island_fails_people():
    c = patrol_ctx()
    c["dump"]["refs"][-1]["pos"] = [3900.0, 3900.0, 800.0]  # the second marker: 400 units past the mesh's edge
    assert any("patrol marker 2 of 2" in x and "off the navmesh" in x for x in C.run(c)["people"])
    c = patrol_ctx()
    c["navs"][k(0x601, W)] = nav(k(0x601, W), "exterior", (1, 0), 4200, 1000, 5000, 3500, 800)  # ground no edge joins
    c["dump"]["refs"][-1]["pos"] = [4500.0, 1600.0, 800.0]
    res = C.run(c)["people"]
    assert any("patrol marker 2 of 2 is not reachable from marker 1" in x for x in res)
    assert any("patrol marker 1 of 2 is not reachable from marker 2" in x for x in res)  # the loop's way back


def test_a_point_is_looked_up_on_the_nearest_surface_of_the_meshes_round_it():
    deck = nav(k(0x602, W), "exterior", (0, 0), 1000, 1000, 3500, 3500, 1000)
    ground = nav(k(0x600, W), "exterior", (0, 0), 1000, 1000, 3500, 3500, 800)
    idx = C.NavIndex({deck.fk: deck, ground.fk: ground})
    assert idx.at("exterior", [2000.0, 2000.0, 990.0])[0] == deck.fk
    assert idx.at("exterior", [2000.0, 2000.0, 805.0])[0] == ground.fk
    assert idx.at("exterior", [3560.0, 2000.0, 800.0]) == (ground.fk, 0)  # 60 units off the edge: the triangle beside it
    assert idx.at("exterior", [3700.0, 2000.0, 800.0]) is None and idx.at("exterior", [2000.0, 2000.0, 1200.0]) is None
    assert idx.at("house", [2000.0, 2000.0, 800.0]) is None


def test_the_nordic_review_outranks_the_rule_and_a_bare_light_passes():
    c = ctx()
    d = c["dump"]["refs"][0]
    d.update(model="meshes/architecture/windhelm/whgroundpiece.nif", base_type="STAT")
    c["plan"]["refs"][0]["base"] = "X.esm:000AAA"
    c["nordic_review"] = {"X.esm:000AAA": {"verdict": "neutral"}}
    assert not C.check_nordic(c)
    c["nordic_review"] = {"X.esm:000AAA": {"verdict": "nordic"}}
    assert C.check_nordic(c)
    d.update(model=None, base_type="LIGH", base_edid="WRFireLightNS")
    c["nordic_review"] = {}
    assert not C.check_nordic(c)
