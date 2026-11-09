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
    plan = {"refs": [hut, door, idoor, bed, work], "cells": [{"x": 0, "y": 0, "cell": k(0x100, W)}],
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
                     dref(work, base_type="STAT", base_edid="XMarkerHeading", bounds=None)],
            "overrides": [{"fk": k(0x500, W), "flags": 0x800}],
            "land": [], "actors": [{"fk": k(11), "base": k(10)}], "cells": [],
            "npcs": [{"fk": k(10), "packages": [k(20), k(21)], "factions": ["ANP_t_CrimeFaction", "ANP_t_vendor", "JobMerchantFaction"],
                      "faction_keys": [k(30), k(31), "Skyrim.esm:051596"], "class": ""}],
            "packages": [{"fk": k(20), "edid": "sleep", "location": k(4)}, {"fk": k(21), "edid": "work", "location": k(5)}],
            "factions": [{"fk": k(30), "vendor": False}, {"fk": k(31), "vendor": True, "chest": k(40)}], "classes": []}
    navs = {k(0x600, W): nav(k(0x600, W), "exterior", (0, 0), 1000, 1000, 3500, 3500, 800, doors=[(0, k(2))]),
            k(50): nav(k(50), "house", None, -200, -200, 600, 600, 0, doors=[(0, k(3))])}
    return {"plan": plan, "dump": dump, "facts": {"cells": [land_cell(0, 0)]}, "navs": navs,
            "gives": [{"give_kind_id": "trader-general", "detail": "trader"}],
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
