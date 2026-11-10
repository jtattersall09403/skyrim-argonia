"""tools/places/edits.py against the shared fixtures, plus property tests (seeded random op lists)."""
import copy
import json
import random
import re
from pathlib import Path

import pytest

from tools.places.edits import (EditConflict, EditError, apply, apply_save, canonical, check_save, invert,
                                load_place, write_place)

FIX = Path(__file__).parent / "places_edits"
PLACE = json.loads((FIX / "place.json").read_text())
CASES = sorted(p.stem for p in FIX.glob("*.json") if p.stem != "place")


@pytest.mark.parametrize("case", CASES)
def test_fixture(case):
    c = json.loads((FIX / f"{case}.json").read_text())
    if "expected" in c:
        assert apply(PLACE, c["ops"]) == c["expected"]
    else:
        with pytest.raises(EditError) as e:
            apply(PLACE, c["ops"])
        assert re.search(c["error"], str(e.value))


def test_pure():
    before = copy.deepcopy(PLACE)
    apply(PLACE, json.loads((FIX / "all_ops.json").read_text())["ops"])
    assert PLACE == before


def random_ops(rng, files, count):
    """Independent ops: each touches a different row, so any order gives the same files."""
    files = canonical(files)
    ops, n = [], 0
    refs = [r for r in files["spaces"]["exterior"]["refs"] if r["id"].startswith("r.")]
    rng.shuffle(refs)
    for r in refs[:count]:
        n += 1
        kind = rng.choice(["move", "remove", "move"])
        if kind == "move":
            after = {"pos": [p + rng.uniform(-200, 200) for p in r["pos"]], "rot": [0, 0, rng.uniform(0, 6.28)]}
            ops.append({"n": n, "op": "ref.move", "space": "exterior", "id": r["id"],
                        "before": {"pos": r["pos"], "rot": r["rot"]}, "after": after})
        else:
            ops.append({"n": n, "op": "ref.remove", "space": "exterior", "id": r["id"], "before": r})
    for i in range(rng.randint(0, 3)):
        n += 1
        ops.append({"n": n, "op": "ref.add", "space": "exterior",
                    "ref": dict(refs[0], id=f"new.{n}", pos=[rng.uniform(0, 4096) for _ in range(3)])})
        n += 1
        ops.append({"n": n, "op": "veg.clear", "space": "exterior",
                    "items": [{"base": "X:000001", "pos": [float(n * 100), 0.0, 0.0]}]})
        n += 1
        ops.append({"n": n, "op": "land.patch", "space": "exterior", "cell": [i, 0],
                    "verts": [[1, 1, 0.0, rng.uniform(-20, 20)]]})
        n += 1
        ops.append({"n": n, "op": "path.add", "space": "exterior",
                    "path": {"id": f"p.{n}", "kind": "path", "points": [[0, 0], [n, n]], "width": 100, "style": "mud"}})
        n += 1
        ops.append({"n": n, "op": "person.add", "space": "exterior", "person": {"id": f"pp.{n}", "name": "x"}})
    return ops


def big_place(rng):
    p = copy.deepcopy(PLACE)
    base = p["spaces"]["exterior"]["refs"][0]
    p["spaces"]["exterior"]["refs"] += [dict(base, id=f"r.{i:03}", pos=[rng.uniform(0, 4096) for _ in range(3)])
                                        for i in range(30)]
    return canonical(p)


@pytest.mark.parametrize("seed", range(25))
def test_inverse_is_identity(seed):
    rng = random.Random(seed)
    files = big_place(rng)
    ops = random_ops(rng, files, 12) + json.loads((FIX / "all_ops.json").read_text())["ops"]
    for i, op in enumerate(ops):
        op["n"] = i + 1
    assert apply(apply(files, ops), invert(ops)) == files


@pytest.mark.parametrize("seed", range(25))
def test_independent_order(seed):
    rng = random.Random(seed)
    files = big_place(rng)
    ops = random_ops(rng, files, 15)
    shuffled = ops[:]
    rng.shuffle(shuffled)
    assert apply(files, ops) == apply(files, shuffled)


def test_save_twice_rejected(tmp_path):
    ops = json.loads((FIX / "all_ops.json").read_text())["ops"]
    save = {"save_id": "s1", "place_id": "fixture", "name": "t", "at": "2026-11-09T00:00:00Z", "final": False,
            "base": {}, "ops": ops}
    write_place(tmp_path / "fixture", PLACE)
    once = apply_save(load_place(tmp_path / "fixture"), save)
    assert once["place"]["saves_applied"] == ["s1"]
    assert once["place"]["preferences"][0]["n"] == 2  # the one taste op
    write_place(tmp_path / "fixture", once)
    assert load_place(tmp_path / "fixture") == once
    with pytest.raises(EditConflict, match="already applied"):
        apply_save(load_place(tmp_path / "fixture"), save)


@pytest.mark.parametrize("bad,msg", [
    ({"place_id": "fixture", "ops": []}, "save_id"),
    ({"save_id": "s", "place_id": "other", "ops": []}, "not 'fixture'"),
    ({"save_id": "s", "place_id": "fixture", "ops": [{"n": 2, "op": "veg.clear", "space": "e", "items": []},
                                                     {"n": 1, "op": "veg.clear", "space": "e", "items": []}]}, "increase"),
    ({"save_id": "s", "place_id": "fixture", "ops": [{"n": 1, "op": "ref.move", "space": "e", "id": "a",
                                                      "before": {"pos": [0, 0, 0]}, "after": {"rot": [0, 0, 0]}}]}, "same fields"),
    ({"save_id": "s", "place_id": "fixture", "ops": [{"n": 1, "op": "veg.clear", "space": "e", "items": [], "call": "meh"}]}, "fault or taste"),
])
def test_schema(bad, msg):
    with pytest.raises(EditError, match=msg):
        check_save(bad, "fixture")


def test_interior_copy_inverse():
    ops = json.loads((FIX / "interior_copy.json").read_text())["ops"]
    files = canonical(PLACE)
    out = apply(files, ops)
    assert out["spaces"]["FixHouse02"]["space"]["door_from"] == "fix.30"
    assert apply(out, invert(ops)) == files


HELSTROM = Path(__file__).resolve().parents[2] / "newworld/places/helstrom"


def helstrom_ops(files):
    """One op of every kind the studio emits, shaped as tools/places/studio/web/js/tools.js and people.js make them."""
    ext = files["spaces"]["exterior"]["refs"]
    ops = []

    def add(op):
        op.setdefault("space", "exterior")
        op["n"] = len(ops) + 1
        ops.append(op)
    for mode in ("ground", "above", "stilts", "on", "water"):
        r = next(x for x in ext if (x.get("seat") or {}).get("mode") == mode)
        before = {"pos": r["pos"], "rot": r["rot"], "scale": r.get("scale", 1), "seat": r["seat"]}
        after = copy.deepcopy(before)
        after["pos"] = [before["pos"][0] + 100, before["pos"][1] - 50, before["pos"][2] + 3]
        after["seat"]["dz"] = after["seat"].get("dz", 0) + 3
        add({"op": "ref.move", "id": r["id"], "before": before, "after": after})
    aligned = next(x for x in ext if "align" in x)
    add({"op": "ref.remove", "id": aligned["id"], "before": aligned, "call": "taste"})
    add({"op": "ref.add", "ref": dict(copy.deepcopy(ext[0]), id="helstrom.TESTADD", pos=[0.0, 0.0, 0.0])})
    add({"op": "veg.restore", "items": [files["clear"][0]]})
    add({"op": "veg.clear", "items": [{"base": "Skyrim.esm:0A7329", "pos": [1.0, 2.0, 3.0]}]})
    add({"op": "land.patch", "cell": [-1, -155], "verts": [[3, 4, 0.0, -20.0]],
         "tool": {"kind": "lower", "radius": 128, "strength": 0.5}})
    walk = next(p for p in files["paths"] if p["kind"] == "walkway")
    add({"op": "path.edit", "path": dict(walk, width=200.0), "before": walk})
    other = next(p for p in files["paths"] if p["id"] != walk["id"])
    add({"op": "path.remove", "path": other, "before": other})
    add({"op": "path.add", "path": {"id": "helstrom.path.TEST", "kind": "street", "points": [[0, 0], [500, 0]],
                                    "width": 256, "style": "dirt"}})
    p0 = files["people"][0]
    p1 = copy.deepcopy(p0)
    p1["routine"][0]["hours"] = 8
    add({"op": "person.edit", "person": p1, "before": p0})
    add({"op": "person.remove", "person": files["people"][1], "before": files["people"][1]})
    add({"op": "person.add", "person": dict(copy.deepcopy(p0), id="helstrom.PTEST")})
    return ops


@pytest.mark.skipif(not HELSTROM.exists(), reason="lane D's Helstrom draft is not on disk")
def test_real_helstrom_every_op_kind():
    files = load_place(HELSTROM)
    ops = helstrom_ops(files)
    out = apply(files, ops)
    assert apply(out, invert(ops)) == files
