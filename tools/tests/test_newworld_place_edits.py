"""Edits of single placed things (tools/newworld/place/edits.py): each changes its own reference and nothing else,
a second run writes nothing, a new placement keeps, re-anchors or reports each edit, and no other reference's
identity or form id moves."""
import json
import os

import pytest

from tools.newworld import rebuild as R
from tools.newworld.place import edits as E
from tools.newworld.place import place as P

OAK, ROCK, PALM = "000A01:Trees.esp", "000B02:Rocks.esp", "000C03:Trees.esp"
BASES = {OAK: ("TreeOak", "canopy_tree"), ROCK: ("RockBig", "boulder"), PALM: ("TreePalm", "palm")}
THINGS = [  # base, x, y: three cell rows (cy 0, 1, 2), cell 0,0 holding four
    (OAK, 500.0, 500.0), (ROCK, 900.0, 600.0), (OAK, 1500.0, 2500.0), (PALM, 3000.0, 3000.0),
    (OAK, 5000.0, 700.0), (ROCK, 600.0, 4500.0), (OAK, 2000.0, 5000.0), (ROCK, 700.0, 8300.0), (PALM, 4200.0, 9000.0)]


def placement(d, things=THINGS, key="k1"):
    d.mkdir(parents=True, exist_ok=True)
    for f in d.glob("cy*.jsonl"):
        f.unlink()
    refs = []
    for base, x, y in things:
        cell = E.cell_of(x, y)
        refs.append({"cell": list(cell), "base": base, "pos": [x, y, 10.0], "rot": [0.0, 0.0, 1.0], "scale": 1.0,
                     "cls": BASES[base][1], "db": BASES[base][0].lower(), "id": P.ident(base, x, y, cell)})
    fids = P.form_ids([r["id"] for r in refs])
    bases = [{"key": k, "ref": f"{k.split(':')[1]}:{e}", "copied": True, "sig": "TREE" if "Tree" in e else "STAT", "model": f"m\\{e}.nif",
              "obnd": [-100, -100, 0, 100, 100, 300], "edid": e, "plugin": k.split(":")[1], "db_id": e.lower(), "cls": c}
             for k, (e, c) in BASES.items()]
    rec = {b["key"]: b for b in bases}
    for cy in (2, 1, 0):
        lines = []
        for r in refs:
            if r["cell"][1] == cy:
                r["fid"] = f"{fids[r['id']]:06X}"
                lines.append(P.shard_line(r, rec[r["base"]]))
        (d / E.shard_name(cy)).write_text("".join(ln + "\n" for ln in lines))
    (d / "bases.json").write_text(json.dumps({"schema": 1, "key": key, "build_id": "b", "bases": bases}, indent=1))
    (d / "manifest.json").write_text(json.dumps({"key": key, "build_id": "b", "refs": len(refs), "shard_sha256": key}))
    return {(r["base"], r["pos"][0], r["pos"][1]): r for r in refs}


@pytest.fixture
def world(tmp_path):
    refs = placement(tmp_path / "placed")
    return {"placed": tmp_path / "placed", "refs": tmp_path / "refs", "edits": tmp_path / "edits.jsonl", "by": refs,
            "id": lambda i: refs[THINGS[i]]["id"]}


def edit(w, op, i=None, **k):
    return E.edit(op, k.pop("by", "owner"), w["edits"], w["placed"], ident=None if i is None else w["id"](i), judge=False,
                  now="2026-11-11T20:00:00Z", **k)


def apply(w):
    return E.apply(w["edits"], w["placed"], w["refs"], log=lambda *_: None)


def lines(d):
    return {json.loads(ln)["id"]: ln for f in sorted(d.glob("cy*.jsonl")) for ln in f.read_text().splitlines()}


def stamps(d):
    return {f.name: (os.stat(f).st_mtime_ns, os.stat(f).st_ino) for f in sorted(d.iterdir())}


def test_an_identity_is_what_the_rules_decided_and_its_form_id_follows_from_it():
    a = P.ident(OAK, 500.04, 500.0, (0, 0))
    assert a == P.ident(OAK.lower(), 500.0, 500.0, [0, 0]) and a.startswith("flora/0,0/") and E.IDENT.fullmatch(a)
    assert len({a, P.ident(ROCK, 500.0, 500.0, (0, 0)), P.ident(OAK, 500.1, 500.0, (0, 0)), P.ident(OAK, 500.0, 500.0, (0, 1))}) == 4
    names = [P.ident(b, x, y, E.cell_of(x, y)) for b, x, y in THINGS]
    ids = P.form_ids(names)
    assert ids == P.form_ids(reversed(names)) and len(set(ids.values())) == len(names)
    assert all(P.FID_FIRST <= v <= P.FID_LAST for v in ids.values())
    fewer = P.form_ids(names[:3] + names[4:])
    assert all(fewer[n] == ids[n] for n in fewer)       # a thing that goes takes no other thing's id with it
    with pytest.raises(ValueError):
        P.form_ids([names[0], names[0]])


def test_no_edits_gives_the_placement_byte_for_byte(world):
    apply(world)
    for f in world["placed"].glob("cy*.jsonl"):
        assert (world["refs"] / f.name).read_bytes() == f.read_bytes()
    assert (world["refs"] / "bases.json").read_bytes() == (world["placed"] / "bases.json").read_bytes()
    man = json.loads((world["refs"] / "manifest.json").read_text())
    assert man["key"] == "k1" and man["refs"] == len(THINGS) and man["edits"]["things"] == 0


def test_each_edit_changes_its_own_reference_and_nothing_else(world):
    apply(world)
    before, was = lines(world["refs"]), stamps(world["refs"])
    edit(world, "remove", 0)
    edit(world, "move", 1, pos=[950.0, 640.0, 12.0], rot=[0.0, 0.0, 2.0], scale=1.2)
    edit(world, "swap", 2, base=PALM)
    got = edit(world, "add", base=ROCK, pos=[2500.0, 1000.0, 7.0])
    rec = apply(world)
    after = lines(world["refs"])
    added = got["row"]["id"]
    assert set(before) - set(after) == {world["id"](0)} and set(after) - set(before) == {added}
    touched = {world["id"](1), world["id"](2)}
    assert all(after[i] == before[i] for i in before if i in after and i not in touched)      # byte for byte
    moved, swapped, new = (json.loads(after[i]) for i in (world["id"](1), world["id"](2), added))
    assert (moved["pos"], moved["rz"], moved["scale"], moved["key"]) == ([950.0, 640.0, 12.0], 2.0, 1.2, ROCK)
    assert (swapped["key"], swapped["base"], swapped["cls"], swapped["model"], swapped["pos"]) == (PALM, "Trees.esp:TreePalm", "palm", "m\\TreePalm.nif", [1500.0, 2500.0, 10.0])
    assert (new["key"], new["cell"], new["cls"], new["x"]) == (ROCK, [0, 0], "boulder", 2500.0)
    # no other reference's form id moves; the moved and swapped things keep theirs; the added one has its own block's
    assert all(json.loads(after[i])["fid"] == json.loads(before[i])["fid"] for i in before if i in after)
    assert E.ADD_FIRST <= int(new["fid"], 16) <= E.ADD_LAST
    # only the row of the cells the edits name was written again
    now = stamps(world["refs"])
    assert now["cy+001.jsonl"] == was["cy+001.jsonl"] and now["cy+002.jsonl"] == was["cy+002.jsonl"] and now["cy+000.jsonl"] != was["cy+000.jsonl"]
    assert rec["by_status"] == {"applied": 4} and len(rec["things"]) == 4
    man = json.loads((world["refs"] / "manifest.json").read_text())
    assert man["key"].startswith("k1+") and man["refs"] == len(THINGS) and man["placed"]["key"] == "k1"


def test_a_second_run_changes_nothing(world):
    edit(world, "remove", 0)
    edit(world, "move", 5, pos=[650.0, 4550.0, 10.0])
    apply(world)
    was = stamps(world["refs"])
    apply(world)
    assert stamps(world["refs"]) == was


def test_a_thing_moved_to_another_row_leaves_its_shard_and_keeps_its_name(world):
    apply(world)
    edit(world, "move", 0, pos=[520.0, 8500.0, 3.0])
    apply(world)
    i = world["id"](0)
    assert i not in (world["refs"] / "cy+000.jsonl").read_text()
    o = json.loads(lines(world["refs"])[i])
    assert o["cell"] == [0, 2] and o["fid"] == world["by"][THINGS[0]]["fid"] and i in (world["refs"] / "cy+002.jsonl").read_text()
    counts = json.loads((world["refs"] / "counts.json").read_text())
    assert counts["0,0"] == 3 and counts["0,2"] == 2


def test_restore_takes_a_thing_back_to_the_rules(world):
    apply(world)
    before = {f.name: f.read_bytes() for f in world["refs"].glob("cy*.jsonl")}
    edit(world, "remove", 3)
    got = edit(world, "add", base=OAK, pos=[100.0, 100.0, 0.0])
    apply(world)
    edit(world, "restore", 3)
    E.edit("restore", "owner", world["edits"], world["placed"], ident=got["row"]["id"], judge=False)
    apply(world)
    assert {f.name: f.read_bytes() for f in world["refs"].glob("cy*.jsonl")} == before
    assert json.loads((world["refs"] / "manifest.json").read_text())["key"] == "k1"
    assert len(world["edits"].read_text().splitlines()) == 4      # the file keeps every row


def test_a_new_placement_keeps_reanchors_or_reports_every_edit(world):
    edit(world, "move", 0, pos=[560.0, 560.0, 10.0])     # its thing stands unchanged in the new placement
    edit(world, "remove", 1)                             # its thing is placed 0.5 m away: the same thing
    edit(world, "remove", 4)                             # its thing is no longer placed; another base stands on its spot
    edit(world, "swap", 6, base=PALM)                    # its thing is no longer placed, nothing near
    source = world["edits"].read_bytes()
    new = [(OAK, 500.0, 500.0), (ROCK, 935.0, 600.0), (OAK, 1500.0, 2500.0), (PALM, 3000.0, 3000.0),
           (ROCK, 5000.0, 700.0), (ROCK, 600.0, 4500.0), (ROCK, 700.0, 8300.0), (PALM, 4200.0, 9000.0), (OAK, 3333.0, 4444.0)]
    fresh = placement(world["placed"], new, key="k2")
    rec = apply(world)
    fate = {r["n"]: r["status"] for r in rec["rows"]}
    assert fate == {1: "applied", 2: "reanchored", 3: "orphaned", 4: "orphaned"}
    assert world["edits"].read_bytes() == source                                  # kept: never dropped, never rewritten
    after = lines(world["refs"])
    assert json.loads(after[world["id"](0)])["pos"] == [560.0, 560.0, 10.0]
    assert fresh[(ROCK, 935.0, 600.0)]["id"] not in after                         # the same rock, half a metre on: removed
    assert fresh[(ROCK, 5000.0, 700.0)]["id"] in after                            # another thing on the spot: never touched
    assert len(after) == len(new) - 1
    assert "no longer place" in next(r["detail"] for r in rec["rows"] if r["n"] == 3)
    # an orphaned row is reported at every run until a restore answers it
    assert E.apply(world["edits"], world["placed"], world["refs"], log=lambda *_: None)["by_status"]["orphaned"] == 2
    E.append(world["edits"], {"n": 5, "op": "restore", "id": world["id"](4), "by": "owner", "tier": E.OWNER_TIER, "at": "t"})
    assert apply(world)["by_status"] == {"applied": 3, "orphaned": 1, "reanchored": 1}


def test_the_owners_edit_stands_above_any_other_tiers(world):
    edit(world, "move", 2, pos=[1600.0, 2500.0, 10.0], by="lane-x")
    edit(world, "move", 2, pos=[1700.0, 2500.0, 10.0])
    with pytest.raises(E.EditError, match="only the owner"):
        edit(world, "remove", 2, by="lane-x")
    row = {"n": 9, "op": "remove", "id": world["id"](2), "base": OAK, "pos": [1700.0, 2500.0, 10.0], "origin": [1500.0, 2500.0],
           "by": "lane-x", "tier": E.AGENT_TIER, "at": "t"}
    E.append(world["edits"], row)                         # written past the door: still not applied
    rec = apply(world)
    assert [r["status"] for r in rec["rows"]] == ["applied", "applied", "held"]
    assert json.loads(lines(world["refs"])[world["id"](2)])["x"] == 1700.0
    with pytest.raises(E.EditError):
        E.validate({**row, "tier": E.OWNER_TIER})         # the owner's tier is the owner's alone


def test_a_rule_an_edit_breaks_is_the_owners_to_confirm_and_another_tiers_to_keep(world, monkeypatch):
    class OnTheRoad:
        def __init__(self, *a):
            pass

        def breaks(self, ident, st):
            return ["road"] if st["pos"][0] == 777.0 else []
    monkeypatch.setattr(E, "Judge", OnTheRoad)
    monkeypatch.setattr(P, "PLACED", world["placed"])
    monkeypatch.setattr(P, "REFS", world["refs"])
    args = dict(ident=world["id"](1), pos=[777.0, 600.0, 10.0], now="t")
    with pytest.raises(E.EditError, match="only the owner may"):
        E.edit("move", "lane-x", world["edits"], world["placed"], **args)
    got = E.edit("move", "owner", world["edits"], world["placed"], **args)
    assert got["breaks"] == ["road"] and not got["appended"] and not world["edits"].exists()
    got = E.edit("move", "owner", world["edits"], world["placed"], confirm=True, **args)
    assert got["appended"] and got["row"]["confirmed"] == ["road"]
    said = []
    assert E.check(world["edits"], log=said.append) == 1 and "run the edits stage" in said[0]     # not applied yet
    apply(world)
    said.clear()
    assert E.check(world["edits"], log=said.append) == 0
    doc = json.loads((world["refs"] / "edits_check.json").read_text())
    assert (doc["confirmed"], doc["to_confirm"], doc["failed"]) == (1, 0, 0) and any("CONFIRMED by the owner" in s for s in said)
    # the same break on a row that does not confirm it is the owner's to confirm, never red; a lower tier's is red
    rows = [json.loads(ln) for ln in world["edits"].read_text().splitlines()]
    rows[0].pop("confirmed")
    world["edits"].write_text(json.dumps(rows[0]) + "\n")
    apply(world)
    assert E.check(world["edits"], log=said.append) == 0 and json.loads((world["refs"] / "edits_check.json").read_text())["to_confirm"] == 1
    world["edits"].write_text(json.dumps({**rows[0], "by": "lane-x", "tier": E.AGENT_TIER}) + "\n")
    apply(world)
    assert E.check(world["edits"], log=said.append) == 1 and any(s.strip().startswith("FAIL flora/") for s in said)


def test_a_thing_is_found_by_identity_form_id_or_position_and_listed_with_both(world):
    r = world["by"][THINGS[1]]
    edit(world, "move", 1, pos=[950.0, 640.0, 12.0])
    for how in ({"fid": r["fid"]}, {"fid": f"ArgoniaNewWorld.esm:{r['fid']}"}, {"at": (950.5, 640.0)}):
        got = E.listing(world["placed"], world["edits"], **how)
        assert [(o["id"], o["fid"], o["pos"], o.get("edited")) for o in got] == [(r["id"], r["fid"], [950.0, 640.0, 12.0], True)]
    cell = E.listing(world["placed"], world["edits"], cell=(0, 0))
    assert len(cell) == 4 and {o["id"] for o in cell} == {world["id"](i) for i in range(4)} and all(o["fid"] and o["base"] for o in cell)
    with pytest.raises(E.EditError):
        E.listing(world["placed"], world["edits"], at=(3900.0, 100.0))
    with pytest.raises(E.EditError, match="outside the world"):
        edit(world, "move", 1, pos=[950.0, 99999.0, 0.0])


def test_what_waits_names_the_rows_the_cells_and_the_places_it_reaches(world, tmp_path):
    apply(world)
    places = tmp_path / "places"
    (places / "tenmal").mkdir(parents=True)
    (places / "tenmal/place.json").write_text("{}")
    (places / "tenmal/clear.jsonl").write_text(json.dumps({"base": "ArgoniaNewWorld.esm:0023A2", "pos": [500.0, 500.0, 10.0]}) + "\n")
    (places / "far").mkdir()
    (places / "far/place.json").write_text("{}")
    (places / "far/clear.jsonl").write_text(json.dumps({"base": "x", "pos": [90000.0, 500.0, 10.0]}) + "\n")
    none = E.pending(world["edits"], world["placed"], world["refs"], places)
    assert none["things"] == [] and none["navmesh_cells"] == []
    edit(world, "remove", 0)
    p = E.pending(world["edits"], world["placed"], world["refs"], places)
    assert p["things"] == [world["id"](0)] and p["shard_rows"] == [0] and p["count_cells"] == [(0, 0)] and p["mist_cells"] == []
    assert (0, 0) in p["navmesh_cells"] and (0, -1) in p["navmesh_cells"] and len(p["navmesh_cells"]) <= 9 and (1, 2) not in p["navmesh_cells"]
    assert p["places"] == {"tenmal": {"clear": 1, "cells": False}} and p["new_bases"] == []
    out = []

    class Out:
        write = staticmethod(out.append)
    E.print_pending(p, file=Out)
    text = "".join(out)
    assert "nothing is placed again" in text and "16 minutes" in text and "tenmal" in text and "Terrain LOD: never" in text
    apply(world)
    assert E.pending(world["edits"], world["placed"], world["refs"], places)["things"] == []


def test_an_edit_makes_stale_only_the_stages_after_the_placement():
    stages = {s.name: s for s in R.STAGES}
    spec = f"src:{R.EDITS_FILE}"
    assert [s.name for s in R.STAGES if spec in s.reads + s.check_reads] == ["edits"]
    reads = R.deps(R.STAGES, waits=False)
    after, grow = {"edits"}, True
    while grow:
        more = {n for n, d in reads.items() if set(d) & after} - after
        after |= more
        grow = bool(more)
    assert {"mist", "navmesh", "map", "esm", "readback"} <= after
    assert not after & {"tools", "scope", "regions", "db", "terrain", "needs", "water", "land", "relief", "landcover", "cells",
                        "landings", "place", "paint", "atmosphere"}
    # the mist reads how many things a cell holds, never which: a move inside a cell does not run it
    assert not any("refs/flora/manifest.json" in r for r in stages["mist"].reads)
    assert "out:newworld/plugin/refs/flora/counts.json" in stages["mist"].reads
    # the placement's own stage never reads the edits, and writes where the edits stage alone reads
    assert all(w.startswith("out:newworld/plugin/placed/flora/") for w in stages["place"].writes)


def test_a_seat_row_lowers_every_thing_of_its_base_and_nothing_else(world, monkeypatch):
    import numpy as np
    from tools.newworld.place import seat as S
    pts = np.array([[0.0, 0.0, 70.0], [10.0, 0.0, 200.0]])     # the mesh's lowest vertex 1 m over its pivot
    monkeypatch.setattr(S, "mesh_points", lambda model, resolver=None: pts)
    monkeypatch.setattr(S.Seater, "ground", lambda self, xs, ys: np.zeros(len(xs)))
    world["edits"].write_text(json.dumps({"n": 1, "op": "seat", "base": "Trees.esp:TreeOak", "to": {"embed_m": 0.1},
                                          "by": "agent", "at": "2026-11-12T00:00:00Z", "tier": "AGENT_INVENTED"}) + "\n")
    rec = apply(world)
    got = {o["id"]: o for d in [world["refs"]] for f in d.glob("cy*.jsonl") for o in map(json.loads, f.read_text().splitlines())}
    for (base, x, y), r in world["by"].items():
        o = got[r["id"]]
        assert o["fid"] == r["fid"] and o["pos"][:2] == [x, y] and o["rot"] == r["rot"]
        assert o["pos"][2] == (-77.0 if base == OAK else 10.0)  # lowest vertex at 80: down 80 + 7
    assert rec["seated"] == {"Trees.esp:TreeOak": 4}
    assert E.load(world["edits"]) == [] and E.seat_rows(world["edits"]) == {"Trees.esp:TreeOak": 0.1}


def test_seat_clearance_poses_the_mesh():
    import numpy as np
    from tools.newworld.place import seat as S
    pts = np.array([[100.0, 0.0, 0.0], [0.0, 0.0, 50.0]])
    # tipped 90 degrees about y: the vertex 100 units along x goes 100 units down
    c = S.clearance(pts, [0.0, 0.0, 500.0], [0.0, np.pi / 2, 0.0], 1.0, lambda xs, ys: np.zeros(len(xs)))
    assert abs(c - 400.0) < 1e-6


def test_a_drop_row_takes_away_every_thing_of_its_base_and_nothing_else(world):
    world["edits"].write_text(json.dumps({"n": 1, "op": "drop", "base": "Trees.esp:TreePalm", "by": "agent",
                                          "at": "2026-11-12T00:00:00Z", "tier": "AGENT_INVENTED"}) + "\n")
    rec = apply(world)
    got = {o["id"]: o for f in world["refs"].glob("cy*.jsonl") for o in map(json.loads, f.read_text().splitlines())}
    assert rec["dropped"] == {"Trees.esp:TreePalm": 2}
    for (base, x, y), r in world["by"].items():
        assert (r["id"] in got) == (base != PALM)
    assert sum(json.loads((world["refs"] / "counts.json").read_text()).values()) == len(THINGS) - 2
