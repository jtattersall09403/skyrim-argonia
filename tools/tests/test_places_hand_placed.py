# ruff: noqa: F811   (the fixture fx is imported and named by each test)
"""A hand's placement is authoritative: a row a committed agent edit (or the owner's finalised save) moved, turned,
sank, dropped, un-dropped, duplicated or edited stands as the hand left it after any draft stage, and the stage's log
names it with what it would have done (tools/places/hands.py `keep_placed`, run by draft/stages.py `run`)."""
import copy
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
from test_places_draft_stages import drafted, fx, rows  # noqa: E402,F401

from tools.places import edits, hands  # noqa: E402
from tools.places.draft import io, stages  # noqa: E402

EXT = "spaces/exterior/refs.jsonl"
_n = [0]


def commit(pdir: Path, ops: list) -> str:
    """The look tool's commit: the ops applied as an agent's edit, kept under agent-edits/."""
    _n[0] += 1
    sid = f"agent-2026112{_n[0]}T000000"
    ops = [dict(op, n=i, stroke=i, call="fault") for i, op in enumerate(ops, 1)]
    save = {"save_id": sid, "place_id": pdir.name, "name": "a hand", "at": "x", "by": "agent", "final": False, "ops": ops}
    out, left = edits.apply_agent_save(edits.load_place(pdir), save)
    assert not left
    edits.write_place(pdir, out)
    (pdir / "agent-edits").mkdir(exist_ok=True)
    (pdir / "agent-edits" / f"{sid}.json").write_text(json.dumps(save))
    return sid


def move(r, dx=0.0, dy=0.0, dz=0.0, rz=0.0):
    keys = [k for k in ("pos", "rot", "seat") if k in r]
    after = copy.deepcopy({k: r[k] for k in keys})
    after["pos"] = [r["pos"][0] + dx, r["pos"][1] + dy, r["pos"][2] + dz]
    if "rot" in after:
        after["rot"] = [after["rot"][0], after["rot"][1], round(after["rot"][2] + rz, 5)]
    if after.get("seat") and "dz" in after["seat"]:
        after["seat"] = dict(after["seat"], dz=round(after["seat"]["dz"] + dz, 3))
    return {"op": "ref.move", "space": "exterior", "id": r["id"], "before": {k: r[k] for k in keys}, "after": after}


def ext(fx):
    return {r["id"]: r for r in rows(fx / "places/fx" / EXT)}


def run(fx, stage):
    logs = []
    stages.run(stage, "fx", fx / "places", fx / "bundles", log=logs.append)
    return logs


def named(logs, rid):
    return [x for x in logs if rid in x and "placed by hand" in x]


def test_seating_keeps_a_house_sunk_by_hand_and_a_piece_raised_by_hand(fx):
    pdir = fx / "places/fx"
    rs = [r for r in rows(pdir / EXT) if r.get("src") and (r.get("seat") or {}).get("mode") in ("ground", "above", "on")]
    down, up = rs[0], rs[1]
    commit(pdir, [move(down, dz=-60.0), move(up, dz=45.0, rz=0.3)])
    hand = ext(fx)
    logs = run(fx, "seating")
    now = ext(fx)
    for r in (down, up):
        assert {k: now[r["id"]].get(k) for k in ("pos", "rot", "seat")} == {k: hand[r["id"]].get(k) for k in ("pos", "rot", "seat")}
        assert named(logs, r["id"]), logs                  # the stage disagreed, and says so
    assert "would have moved it" in named(logs, down["id"])[0]


def _adds(fx, extra):
    pj = fx / "places/fx/place.json"
    place = json.loads(pj.read_text())
    place["draft"]["add"] = (place["draft"].get("add") or []) + extra
    pj.write_text(json.dumps(place, indent=1) + "\n")
    run(fx, "add")
    return json.loads(pj.read_text())


def test_add_follows_a_hand_moved_door_keeps_a_dropped_piece_out_and_ids_stand_when_a_row_is_inserted(fx):
    pdir = fx / "places/fx"
    n = len(json.loads((pdir / "place.json").read_text())["draft"].get("add") or [])
    place = _adds(fx, [{"base": "T.esm:000001", "kind": "building", "pos": [40500, 1500], "why": "a hall"},
                       {"base": "T.esm:000005", "kind": "door", "pos": [40500, 1240], "why": "a door"},
                       {"base": "T.esm:000001", "kind": "building", "pos": [41200, 1500], "why": "a shed"}])
    hall, door, shed = (io.mint("fx", "add", str(n + i), b) for i, b in enumerate(("T.esm:000001", "T.esm:000005", "T.esm:000001")))
    have = ext(fx)
    assert {hall, door, shed} <= set(have)
    commit(pdir, [move(have[door], dx=70.0, dz=-8.0, rz=0.5),
                  {"op": "ref.remove", "space": "exterior", "id": shed, "before": have[shed]}])
    place = json.loads((pdir / "place.json").read_text())
    row = place["draft"]["add"][n + 1]
    assert row["pos"] == [40570.0, 1240.0] and row["rot_z"] == 0.5 and place["draft"]["add"][n + 2]["dropped"]
    hand = ext(fx)
    logs = run(fx, "add")
    now = ext(fx)
    assert now[door] == hand[door] and shed not in now
    assert all("turned" not in x for x in named(logs, door)), logs   # its source row follows the hand's turn and spot
    # a row inserted mid-list: every other id stays
    place["draft"]["add"].insert(n, {"base": "T.esm:000005", "kind": "door", "pos": [40800, 1240], "why": "inserted"})
    (pdir / "place.json").write_text(json.dumps(place, indent=1) + "\n")
    run(fx, "add")
    now = ext(fx)
    assert now[door] == hand[door] and hall in now and shed not in now
    assert sum(1 for r in now.values() if r.get("why") == "inserted") == 1


def test_add_keeps_a_hand_moved_added_piece_even_against_its_source_row(fx):
    """Where the source row was not followed (it says another spot), the rule still keeps the hand's place."""
    pdir = fx / "places/fx"
    n = len(json.loads((pdir / "place.json").read_text())["draft"].get("add") or [])
    _adds(fx, [{"base": "T.esm:000005", "kind": "door", "pos": [40500, 1240], "why": "a door"}])
    door = io.mint("fx", "add", str(n), "T.esm:000005")
    commit(pdir, [move(ext(fx)[door], dx=-120.0)])
    pj = pdir / "place.json"
    place = json.loads(pj.read_text())
    place["draft"]["add"][n]["pos"] = [40500, 1240]        # a drafter puts the old spot back in the source row
    pj.write_text(json.dumps(place, indent=1) + "\n")
    hand = ext(fx)
    logs = run(fx, "add")
    assert ext(fx)[door]["pos"] == hand[door]["pos"] and "moved it 120 units" in named(logs, door)[0]


def _fake(monkeypatch, stage, fn):
    """A stage that rewrites the rows it owns as its rule gives them, whatever stands (what the real stages did)."""
    monkeypatch.setitem(stages.RUN, stage, fn)


def test_pieces_keeps_a_drop_an_undrop_and_a_duplicate(fx, monkeypatch):
    pdir = fx / "places/fx"
    rs = [r for r in rows(pdir / EXT) if r.get("src")]
    gone, back = rs[2], rs[3]
    commit(pdir, [{"op": "ref.remove", "space": "exterior", "id": back["id"], "before": back}])
    dup = dict(copy.deepcopy(rs[4]), id="fx.LOOK001DUP", pos=[rs[4]["pos"][0] + 200, rs[4]["pos"][1], rs[4]["pos"][2]])
    commit(pdir, [{"op": "ref.remove", "space": "exterior", "id": gone["id"], "before": gone},
                  {"op": "ref.add", "space": "exterior", "ref": back},          # un-dropped by a later hand
                  {"op": "ref.add", "space": "exterior", "ref": dup}])
    hand = ext(fx)

    def pieces(st, log=print):     # puts back every source piece, drops what is not the source's, moves `back`
        st.ext[:] = [r for r in st.ext if r["id"] != dup["id"]] + [copy.deepcopy(gone)]
        for r in st.ext:
            if r["id"] == back["id"]:
                r["pos"] = [r["pos"][0] + 300, r["pos"][1], r["pos"][2]]
    _fake(monkeypatch, "pieces", pieces)
    logs = run(fx, "pieces")
    now = ext(fx)
    assert gone["id"] not in now and now[back["id"]] == hand[back["id"]] and now[dup["id"]] == hand[dup["id"]]
    assert all(named(logs, i) for i in (gone["id"], back["id"], dup["id"])), logs


def test_streets_keeps_a_hand_laid_flight_a_hand_edited_path_and_a_door_set_down_by_hand(fx, monkeypatch):
    pdir = fx / "places/fx"
    have = ext(fx)
    door = next(r for r in have.values() if (r.get("door") or {}).get("arrival")) if any(
        (r.get("door") or {}).get("arrival") for r in have.values()) else None
    flight = {"id": "fx.LOOK001STEPS", "base": "T.esm:000001", "kind": "building", "pos": [40100.0, 1100.0, 10.0],
              "rot": [0.0, 0.0, 1.0], "scale": 1.0, "seat": {"mode": "free"}, "why": "steps laid by hand"}
    path = rows(pdir / "paths.jsonl")[0]
    edited = dict(path, points=[[1.0, 2.0], [3.0, 4.0]])
    ops = [{"op": "ref.add", "space": "exterior", "ref": flight},
           {"op": "path.edit", "path": edited, "before": path}]
    if door is not None:   # an arrival moved by hand: the door row set down again with its own arrival
        moved = copy.deepcopy(door)
        moved["door"]["arrival"] = [moved["door"]["arrival"][0] + 50, moved["door"]["arrival"][1], moved["door"]["arrival"][2]]
        ops += [{"op": "ref.remove", "space": "exterior", "id": door["id"], "before": door},
                {"op": "ref.add", "space": "exterior", "ref": moved}]
    commit(pdir, ops)
    hand, hpaths = ext(fx), {p["id"]: p for p in rows(pdir / "paths.jsonl")}

    def streets(place_id, places, log=print):    # relays the flights it lays, re-lays every path, re-seats arrivals
        p = places / place_id
        rs = [r for r in rows(p / EXT) if r["id"] != flight["id"]]
        for r in rs:
            if (r.get("door") or {}).get("arrival"):
                r["door"] = dict(r["door"], arrival=[0.0, 0.0, 0.0])
        io.write_jsonl(p / EXT, rs)
        io.write_jsonl(p / "paths.jsonl", [dict(q, points=[[9.0, 9.0], [8.0, 8.0]]) for q in rows(p / "paths.jsonl")])
    monkeypatch.setattr(stages, "streets", streets)
    logs = run(fx, "streets")
    now, paths = ext(fx), {p["id"]: p for p in rows(pdir / "paths.jsonl")}
    assert now[flight["id"]] == hand[flight["id"]] and paths[path["id"]] == hpaths[path["id"]]
    assert named(logs, flight["id"]) and named(logs, path["id"])
    if door is not None:
        assert now[door["id"]]["door"] == hand[door["id"]]["door"]


def test_lights_sap_and_people_keep_what_a_hand_moved(fx, monkeypatch):
    pdir = fx / "places/fx"
    rs = rows(pdir / EXT)
    pool = dict(copy.deepcopy(rs[0]), id="fx.sap.T1", kind="activator", src=None, seat={"mode": "ground", "dz": 0.0})
    lamp = dict(copy.deepcopy(rs[0]), id="fx.light.L1", kind="light", src=None, seat={"mode": "free"})
    commit(pdir, [{"op": "ref.add", "space": "exterior", "ref": pool}, {"op": "ref.add", "space": "exterior", "ref": lamp}])
    folk = rows(pdir / "people.jsonl")
    person = folk[0]
    stop = dict(copy.deepcopy(person), work={"space": "exterior", "pos": [123.0, 456.0, 0.0]})
    commit(pdir, [move(ext(fx)[pool["id"]], dx=40.0, dy=-25.0), move(ext(fx)[lamp["id"]], dz=30.0),
                  {"op": "person.edit", "person": stop, "before": person}])
    hand, hfolk = ext(fx), {p["id"]: p for p in rows(pdir / "people.jsonl")}

    def regen(st, log=print):      # the pool at its Hist's roots, the light on its fixture
        for r in st.ext:
            if r["id"] in (pool["id"], lamp["id"]):
                r["pos"] = list(rs[0]["pos"])

    def stops(st, log=print):      # the person at the stop's own spot, named from the people source
        for p in st.files["people"]:
            if p["id"] == person["id"]:
                p["work"] = {"space": "exterior", "pos": [0.0, 0.0, 0.0]}
                p["name"] = "Renamed By The Stage"
    _fake(monkeypatch, "sap", regen)
    _fake(monkeypatch, "lights", regen)
    _fake(monkeypatch, "people", stops)
    logs = run(fx, "sap") + run(fx, "lights") + run(fx, "people")
    now, nfolk = ext(fx), {p["id"]: p for p in rows(pdir / "people.jsonl")}
    assert now[pool["id"]]["pos"] == hand[pool["id"]]["pos"] and now[lamp["id"]]["pos"] == hand[lamp["id"]]["pos"]
    assert nfolk[person["id"]]["work"] == hfolk[person["id"]]["work"]
    assert nfolk[person["id"]]["name"] == "Renamed By The Stage"      # a field the hand did not set stays the stage's
    assert named(logs, pool["id"]) and named(logs, lamp["id"]) and named(logs, person["id"])


def test_a_released_row_goes_back_to_the_stages(fx, monkeypatch):
    pdir = fx / "places/fx"
    r = next(r for r in rows(pdir / EXT) if r.get("src"))
    from tools.places.look import verbs
    commit(pdir, [move(r, dx=90.0)])
    assert (EXT, r["id"]) in hands.placed(pdir)
    assert verbs.release("fx", [r["id"], "-m", "back to the fit"], places=fx / "places")["released"] == r["id"]
    assert (EXT, r["id"]) not in hands.placed(pdir)
    assert not named(run(fx, "seating"), r["id"])
    commit(pdir, [move(ext(fx)[r["id"]], dy=10.0)])             # a hand moves it again: it is held again
    assert (EXT, r["id"]) in hands.placed(pdir)


@pytest.mark.parametrize("stage", ["seating", "add", "names"])
def test_a_stage_that_agrees_with_the_hands_logs_nothing(fx, stage):
    pdir = fx / "places/fx"
    r = next(r for r in rows(pdir / EXT) if r.get("src") and r.get("kind") != "building")
    commit(pdir, [move(r, rz=0.0)])
    assert not [x for x in run(fx, stage) if "placed by hand" in x]


def test_a_stage_that_only_repins_a_hand_rows_seat_keeps_it_where_the_hand_put_it():
    old = {"id": "a", "pos": [1.0, 2.0, 30.0], "seat": {"mode": "above", "dz": 10.0}}
    assert hands.repinned(old, dict(old, seat={"mode": "above", "dz": 115.0}))       # same pose, ground dug under it
    assert not hands.repinned(old, dict(old, pos=[1.0, 2.0, 50.0], seat={"mode": "above", "dz": 30.0}))   # moved
    assert not hands.repinned(old, dict(old, seat={"mode": "stilts", "dz": 10.0}))   # another rule
    assert not hands.repinned(old, dict(old))
