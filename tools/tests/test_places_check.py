"""tools/places/check.py: a small synthetic place passes every check, and one broken fixture per check fails it.

The fixture is made here (no game data): one exterior cell with flat ground at z 800, a hut, a door paired with an
interior door, one person with an owned bed and two stops, one navmesh per space, a cleared plant, a path."""
import base64
import copy
import sys
from pathlib import Path

import numpy as np
import pytest

from tools.navmesh import nvnm
from tools.places import check as C

sys.path.insert(0, str(Path(__file__).parent))
import stock_fixture as SF  # noqa: E402

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


def with_jail(c):
    """The fixture's town with a jail as vanilla's holds have one: the crime faction names the exterior prison marker
    (JAIL, WAIT) and two evidence chests in the house (STOL, PLCN); the markers' teleports lead to each other."""
    d, p = c["dump"], c["plan"]
    crime = k(30)
    jail = {"exterior": k(60), "marker": k(61), "stolen": k(62), "inventory": k(63), "space": "house"}
    p["people"]["crime_faction"] = {"fk": crime, "edid": "ANP_t_CrimeFaction", "jail": jail}
    rows = [{"fk": k(60), "id": "t.release", "kind": "marker", "space": "exterior", "pos": [2000.0, 1500.0, 800.0],
             "rot": [0, 0, 0], "seat": {"mode": "free"}},
            {"fk": k(61), "id": "t.jailmarker", "kind": "marker", "space": "house", "pos": [100.0, 100.0, 0.0], "rot": [0, 0, 0]},
            {"fk": k(62), "id": "t.stolen", "kind": "container", "space": "house", "pos": [0.0, 300.0, 0.0], "rot": [0, 0, 0]},
            {"fk": k(63), "id": "t.inventory", "kind": "container", "space": "house", "pos": [0.0, 400.0, 0.0], "rot": [0, 0, 0]}]
    p["refs"] += rows
    base = {"base": "Skyrim.esm:000004", "base_type": "DOOR", "base_edid": "PrisonMarker", "model": None, "rot": [0, 0, 0],
            "scale": 1.0, "flags": 0x400, "persistent": True, "bounds": None}
    d["refs"] += [{**base, "fk": k(60), "pos": rows[0]["pos"], "space": "exterior",
                   "door": {"to_ref": k(61), "to_pos": [100.0, 100.0, 0.0], "to_rot": [0, 0, 0]}},
                  {**base, "fk": k(61), "pos": rows[1]["pos"], "space": "house",
                   "door": {"to_ref": k(60), "to_pos": [2000.0, 1500.0, 800.0], "to_rot": [0, 0, 0]}},
                  {"fk": k(62), "base": "Skyrim.esm:0267E7", "base_type": "CONT", "pos": rows[2]["pos"], "rot": [0, 0, 0], "scale": 1.0,
                   "flags": 0x400, "space": "house", "owner": crime, "contents": [], "respawns": False, "bounds": None},
                  {"fk": k(63), "base": "Skyrim.esm:108D36", "base_type": "CONT", "pos": rows[3]["pos"], "rot": [0, 0, 0], "scale": 1.0,
                   "flags": 0x400, "space": "house", "owner": crime, "contents": [], "respawns": False, "bounds": None}]
    f = next(x for x in d["factions"] if x["fk"] == crime)
    f.update({"jail": k(60), "wait": k(60), "stolen": k(62), "inventory": k(63), "arrest": True,
              "flag_names": "TrackCrime, CrimeGoldUseDefaults, CanBeOwner"})
    return c


def test_a_jail_as_vanilla_passes_and_a_place_without_one_fines_only():
    res = C.run(with_jail(ctx()))
    assert not any(res.values()), res
    C.run(ctx())
    assert any("fines only" in n for n in C.NOTES) is False  # a place with no crime faction says nothing
    c = ctx()
    c["plan"]["people"]["crime_faction"] = {"fk": k(30), "edid": "ANP_t_CrimeFaction"}
    assert not C.run(c)["jail"] and any("fines only" in n for n in C.NOTES)
    c["dump"]["npcs"][0]["faction_keys"].append("Skyrim.esm:02BE3B")  # a jail-less town's guard offering "go to jail"
    c["plan"]["people"]["npcs"][0]["role"] = "guard"
    assert C.check_jail(c)


@pytest.mark.parametrize("what", ["unset", "off_mesh", "release", "chest", "guard"])
def test_a_broken_jail_fails(what):
    c = with_jail(ctx())
    d = c["dump"]
    if what == "unset":
        next(x for x in d["factions"] if x["fk"] == k(30))["stolen"] = ""
    elif what == "off_mesh":
        next(x for x in d["refs"] if x["fk"] == k(61))["pos"] = [5000.0, 5000.0, 0.0]
    elif what == "release":
        next(x for x in d["refs"] if x["fk"] == k(61))["door"]["to_pos"] = [9000.0, 9000.0, 800.0]
    elif what == "chest":
        next(x for x in d["refs"] if x["fk"] == k(62))["respawns"] = True
    elif what == "guard":
        c["plan"]["people"]["npcs"][0]["role"] = "guard"
    assert C.check_jail(c), what


def with_owing(c):
    """The fixture's town keeping native law: the crime faction names the return spot's prison marker (JAIL, WAIT)
    and the stolen goods chest under the ground (STOL); the return and work markers lead to each other outside; the
    worker's mat by the work spot; the Owing's line first in vanilla's go-to-jail topic."""
    from tools.places.people import GO_TO_JAIL, OWING_PROMPT
    d, p = c["dump"], c["plan"]
    crime = k(30)
    owing = {"topic": GO_TO_JAIL, "info": k(0x80), "prompt": OWING_PROMPT}
    jail = {"exterior": k(60), "wait": k(60), "marker": k(61), "stolen": k(62), "bed": k(64), "space": "exterior", "owing": owing}
    p["people"]["crime_faction"] = {"fk": crime, "edid": "ANP_t_CrimeFaction", "law": "native", "jail": jail}
    pos = {60: [2050.0, 1520.0, 800.0], 61: [2000.0, 1500.0, 800.0], 62: [2050.0, 1520.0, -1248.0], 64: [2000.0, 1650.0, 800.0]}
    p["refs"] += [{"fk": k(n), "id": f"t.owing{n}", "kind": kind, "space": "exterior", "pos": pos[n], "rot": [0, 0, 0],
                   "seat": {"mode": "free"}} for n, kind in ((60, "marker"), (61, "marker"), (62, "container"), (64, "furniture"))]
    base = {"base": "Skyrim.esm:000004", "base_type": "DOOR", "base_edid": "PrisonMarker", "model": None, "rot": [0, 0, 0],
            "scale": 1.0, "flags": 0x400, "persistent": True, "bounds": None, "space": "exterior"}
    d["refs"] += [{**base, "fk": k(60), "pos": pos[60], "door": {"to_ref": k(61), "to_pos": pos[61], "to_rot": [0, 0, 0]}},
                  {**base, "fk": k(61), "pos": pos[61], "door": {"to_ref": k(60), "to_pos": pos[60], "to_rot": [0, 0, 0]}},
                  {"fk": k(62), "base": "Skyrim.esm:0267E7", "base_type": "CONT", "pos": pos[62], "rot": [0, 0, 0], "scale": 1.0,
                   "flags": 0x400, "space": "exterior", "owner": crime, "contents": [], "respawns": False, "bounds": None},
                  {"fk": k(64), "base": "Skyrim.esm:036ED3", "base_type": "FURN", "pos": pos[64], "rot": [0, 0, 0], "scale": 1.0,
                   "flags": 0x400, "space": "exterior", "bounds": None}]
    f = next(x for x in d["factions"] if x["fk"] == crime)
    f.update({"jail": k(60), "wait": k(60), "stolen": k(62), "inventory": "", "arrest": True,
              "flag_names": "TrackCrime, CrimeGoldUseDefaults, CanBeOwner"})
    info = {"fk": k(0x80), "prompt": OWING_PROMPT, "previous": "", "text": ["..."], "link_to": [],
            "conditions": [{"fn": "GetInFaction", "run_on": "Subject", "op": "EqualTo", "value": 1.0, "faction": crime}],
            "scripts": [{"name": "TIF__00020F99", "props": []}], "fragment": {"file": "TIF__00020F99", "on_end": "Fragment_0"}}
    d.setdefault("topics", []).append({"fk": GO_TO_JAIL, "edid": "DGCrimeGoToJail", "infos": [info]})
    # the resist line: the guards take no surrender
    from tools.places.people import RESIST_SCRIPT, RESIST_TOPIC
    guards = k(31)
    jail["resist"] = {"topic": RESIST_TOPIC, "info": k(0x81), "script": RESIST_SCRIPT, "guards": guards}
    rinfo = {"fk": k(0x81), "prompt": "", "previous": "", "text": ["..."], "link_to": [],
             "conditions": [{"fn": "GetInFaction", "run_on": "Subject", "op": "EqualTo", "value": 1.0, "faction": crime}],
             "scripts": [{"name": RESIST_SCRIPT, "props": [{"name": "Guards", "value": guards}]}],
             "fragment": {"file": RESIST_SCRIPT, "on_begin": "Fragment_0", "on_end": None}}
    d["topics"].append({"fk": RESIST_TOPIC, "edid": "DGCrimeResistArrest", "infos": [rinfo]})
    return c


def test_native_laws_owing_as_built_passes():
    res = C.run(with_owing(ctx()))
    assert not res["jail"], res["jail"]


@pytest.mark.parametrize("what", ["missing", "inventory", "reach", "line", "late", "anyone", "fragment", "mat"])
def test_a_broken_owing_fails(what):
    c = with_owing(ctx())
    d = c["dump"]
    info = d["topics"][-2]["infos"][0]
    if what == "missing":
        c["plan"]["people"]["crime_faction"]["jail"] = None
    elif what == "inventory":
        next(x for x in d["factions"] if x["fk"] == k(30))["inventory"] = k(62)
    elif what == "reach":
        next(x for x in d["refs"] if x["fk"] == k(62))["pos"] = [2050.0, 1520.0, 760.0]
    elif what == "line":
        d["topics"][-2]["infos"] = []
    elif what == "late":
        info["previous"] = "Skyrim.esm:0267E1"
    elif what == "anyone":
        info["conditions"] = []
    elif what == "fragment":
        info["fragment"] = {"file": "TIF__000267E1"}
    elif what == "mat":
        next(x for x in d["refs"] if x["fk"] == k(64))["pos"] = [2600.0, 1500.0, 800.0]
    assert C.check_jail(c), what


@pytest.mark.parametrize("what", ["missing", "late", "anyone", "fragment", "guards"])
def test_a_native_resist_that_takes_a_surrender_fails(what):
    c = with_owing(ctx())
    rinfo = c["dump"]["topics"][-1]["infos"][0]
    if what == "missing":
        c["dump"]["topics"][-1]["infos"] = []
    elif what == "late":
        rinfo["previous"] = "Skyrim.esm:0267E2"
    elif what == "anyone":
        rinfo["conditions"] = []
    elif what == "fragment":
        rinfo["fragment"] = {"file": "TIF__000267E2", "on_begin": "Fragment_0"}
    elif what == "guards":
        rinfo["scripts"][0]["props"] = []
    probs = C.check_jail(c)
    assert any("resist" in p for p in probs), (what, probs)


def test_a_foreign_law_keeps_vanillas_yield():
    """A foreign law's faction carries no resist line of ours: one there fails."""
    c = with_owing(ctx())
    assert C.resist_problems(c, c["plan"]["people"]["crime_faction"], {}, native=False) != []
    c["dump"]["topics"][-1]["infos"] = []
    assert C.resist_problems(c, c["plan"]["people"]["crime_faction"], {}, native=False) == []


def with_primitives(c, built=True, why="a trigger of the source's quest"):
    """A collision marker outside built with its source's box; a trigger in the copied house dropped with its reason."""
    box = {"type": "Box", "bounds": [100.0, 8.0, 200.0], "color": [255, 255, 0], "unknown": 0.0}
    c["plan"]["refs"].append({"fk": k(70), "id": "t.wall", "kind": "marker", "space": "exterior", "src": "X.esm:000070",
                              "pos": [1500.0, 3000.0, 800.0], "rot": [0, 0, 0], "seat": {"mode": "free"}})
    c["dump"]["refs"].append({"fk": k(70), "base": "Skyrim.esm:000021", "base_type": "STAT", "pos": [1500.0, 3000.0, 800.0],
                              "rot": [0, 0, 0], "scale": 1.0, "flags": 0, "space": "exterior", "bounds": None,
                              **({"primitive": box} if built else {})})
    c["plan"]["interiors"] = [{"space": "house", "copy_of": "x/house"}]
    trig = {"id": "X.esm:000071", "primitive": {**box, "color": [204, 76, 51]}}
    c["primitive_inputs"] = ({"exterior": [{"id": "X.esm:000070", "primitive": box}], "house": [trig]},
                             [{"src": "X.esm:000070", "space": "exterior", "status": "placed", "as": "t.wall"},
                              {"src": "X.esm:000071", "space": "house", "copy": "house", "status": "dropped", "why": why}],
                             {"house": {"X.esm:000071"}})
    return c


def test_a_primitive_built_identical_or_dropped_with_its_reason_passes():
    c = with_primitives(ctx())
    assert not C.check_primitives(c) and c["primitives"] == {"written": 1, "dropped": 1}
    assert C.check_primitives(with_primitives(ctx(), built=False))
    assert C.check_primitives(with_primitives(ctx(), why=""))


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
        c["source_bases"] = set()
    elif name == "rooms":  # the house copies a source room whose lantern light was not built
        p["interiors"] = [{"space": "house", "copy": {"plugin": "X.esm"}, "copy_of": "x/house"}]
        c["room_refs"] = {"x/house": [{"id": "X.esm:000001", "kind": "door", "pos": [100.0, 0.0, 0.0]},
                                      {"id": "X.esm:000002", "kind": "light", "pos": [0.0, 0.0, 200.0]}]}
    elif name == "levelled":
        d["levelled"].append("ANP_t_person -> Skyrim.esm:09AF07 LItemMiscVendorArmor75")
    elif name == "stock":
        c["stock"] = SF.stock()
        c["stock"]["built"]["containers"][("house", "X.esm:000009")]["contents"].append((SF.DAGGER, 1))
    elif name == "promises":
        c["stock"] = SF.stock()
        c["stock"]["deliveries"][0]["status"] = "open"
    elif name == "jail":
        c = with_jail(c)
        next(x for x in c["dump"]["factions"] if x["fk"] == k(30))["jail"] = ""
    elif name == "primitives":
        c = with_primitives(c, built=False)
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
    """The good fixture plus a boat stop: a boatman of ours in a boatman faction, the network's one route from the
    place to Truowa (20 gold), and his line to Truowa's arrival point."""
    c = copy.deepcopy(ctx())
    c["place_id"] = "t"
    d = c["dump"]
    boat_f = k(0x70)
    d["factions"].append({"fk": boat_f, "edid": "ANP_t_Boatman_boater", "vendor": False})
    d["npcs"][0]["faction_keys"].append(boat_f)
    d["npcs"][0]["factions"].append("ANP_t_Boatman_boater")
    marker, julo = k(0x67, W), k(0x68, W)
    d["world_markers"] = {marker: "ANW_MapMarker_truowa", julo: "ANW_MapMarker_julo", k(0x69, W): f"ANW_MapMarker_{c['place_id']}"}
    props = [{"name": "Destination", "value": marker}, {"name": "Fare", "value": 20}, {"name": "Gold001", "value": "Skyrim.esm:00000F"}]
    info = {"fk": k(0x72), "prompt": "Take me to Truowa (20 gold).", "text": ["Truowa, then."], "link_to": [],
            "conditions": [{"fn": "GetInFaction", "run_on": "Subject", "op": "EqualTo", "value": 1.0, "faction": boat_f},
                           {"fn": "GetGold", "run_on": "Target", "op": "GreaterThanOrEqualTo", "value": 20.0}],
            "scripts": [{"name": "TIF_ARG_BoatTravel", "props": props}], "fragment": {"file": "TIF_ARG_BoatTravel", "on_end": "Fragment_0"}}
    d["topics"] = [{"fk": k(0x71), "edid": "ANP_t_Boat_Truowa", "name": info["prompt"], "quest": k(0x73), "branch": k(0x74), "infos": [info]}]
    c["routes"] = {"boat": [{"to_place_id": "truowa", "fare": 20}]}
    c["gives"].append({"give_kind_id": "boat-stop", "detail": "raft-masters at the landing"})
    if what == "no_destination":
        c["routes"]["boat"].append({"to_place_id": "julo", "fare": 25})
    elif what == "no_script":
        info["scripts"] = []
    elif what == "wrong_fare":
        props[1]["value"] = 25
        info["conditions"][1]["value"] = 25.0
    elif what == "no_gold_condition":
        info["conditions"].pop()
    elif what == "no_faction_condition":
        info["conditions"].pop(0)
    elif what == "wrong_marker":
        props[0]["value"] = julo
    elif what == "no_fragment":
        info["fragment"] = None
    elif what == "no_boatman":
        d["npcs"][0]["faction_keys"].remove(boat_f)
    elif what == "no_route":
        c["routes"] = {}
    elif what == "no_arrival_here":
        del d["world_markers"][k(0x69, W)]
    elif what == "waiting":   # a route to a place the world gives no arrival point yet: not offered, not a failure
        c["routes"]["boat"].append({"to_place_id": "nowhere", "fare": 30})
    return c


def test_a_boat_stop_with_a_line_per_route_passes_services():
    assert not C.run(boat_ctx())["services"]


def test_a_route_to_a_place_with_no_arrival_point_waits_and_passes():
    C.WARNINGS.clear()
    assert not C.run(boat_ctx("waiting"))["services"]
    assert any("nowhere waits on that place" in x for x in C.WARNINGS)


@pytest.mark.parametrize("what", ["no_destination", "no_script", "wrong_fare", "no_gold_condition", "no_faction_condition",
                                  "wrong_marker", "no_fragment", "no_boatman", "no_route", "no_arrival_here"])
def test_a_broken_boat_stop_fails_services(what):
    got = C.run(boat_ctx(what))["services"]
    assert any("boat-stop" in x for x in got), (what, got)


def test_the_network_is_whole_and_its_fares_fixed():
    """The built network: no fast-travel promise, every route between stops of its mode at its fare, one network."""
    from tools.argonia_world import db
    from tools.newworld import travel
    w = db.open("newworld")
    assert travel.problems(w) == []
    boat = {"fare_base": 10, "fare_per_km": 8, "fare_step": 5, "fare_min": 10, "fare_max": 60}
    assert [travel.fare(boat, d) for d in (0, 1200, 2300, 3700, 9000)] == [10, 20, 30, 40, 60]



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
