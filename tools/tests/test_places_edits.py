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
    gone = next(x for x in ext if x.get("kind") == "door")     # a row with a door block: the fullest row shape
    add({"op": "ref.remove", "id": gone["id"], "before": gone, "call": "taste"})
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


COPY = FIX / "copy_refs"   # a copied room's unlisted refs, resolved by the given source (not yet read by the JS mirror)


@pytest.mark.parametrize("case", sorted(p.stem for p in COPY.glob("*.json")))
def test_copy_ref_fixture(case):
    c = json.loads((COPY / f"{case}.json").read_text())
    if "expected" in c:
        assert apply(PLACE, c["ops"], c["source"]) == c["expected"]
    else:
        with pytest.raises(EditError) as e:
            apply(PLACE, c["ops"], c["source"])
        assert re.search(c["error"], str(e.value))


def test_copy_ref_needs_source():
    c = json.loads((COPY / "copy_move.json").read_text())
    with pytest.raises(EditConflict):
        apply(PLACE, c["ops"])


def test_write_place_removes_a_dropped_space(tmp_path):
    from tools.places import edits
    files = {"place": {"place_id": "p"}, "spaces": {"exterior": {"refs": [], "space": None},
                                                    "room": {"refs": [], "space": {"space_id": "room"}}},
             "clear": [], "land": [], "paths": [], "people": []}
    edits.write_place(tmp_path, files)
    assert (tmp_path / "spaces" / "room" / "space.json").exists()
    del files["spaces"]["room"]
    edits.write_place(tmp_path, files)
    assert not (tmp_path / "spaces" / "room").exists() and (tmp_path / "spaces" / "exterior").exists()


def test_a_malformed_op_is_an_edit_error():
    import pytest

    from tools.places import edits
    for op in ({"n": 1, "op": "land.patch", "space": "exterior", "cell": [0, 0], "verts": [["a", 1, 0, 1]]},
               {"n": 1, "op": "land.patch", "space": "exterior", "cell": [0, 0], "verts": [[1.5, 1, 0, 1]]},
               {"n": 1, "op": "land.patch", "space": "exterior", "cell": [0, 0], "verts": [[1, 2, None, 1]]},
               {"n": 1, "op": "veg.clear", "space": "exterior", "items": ["x"]},
               {"n": 1, "op": "veg.clear", "space": "exterior", "items": [{"base": "b", "pos": 3}]}):
        with pytest.raises(edits.EditError):
            edits.check_op(op)


STOCK = FIX / "stock"   # the content ops (identity.edit, stock.*) on a people and a stock source (base.json)
STOCK_BASE = json.loads((STOCK / "base.json").read_text())


def stock_files():
    return copy.deepcopy(PLACE) | copy.deepcopy(STOCK_BASE)


@pytest.mark.parametrize("case", sorted(p.stem for p in STOCK.glob("*.json") if p.stem != "base"))
def test_content_fixture(case):
    from tools.places.edits import canonical_source
    c = json.loads((STOCK / f"{case}.json").read_text())
    files = stock_files()
    if "error" in c:
        with pytest.raises(EditError) as e:
            apply(files, c["ops"])
        assert re.search(c["error"], str(e.value))
        return
    out = apply(files, c["ops"])
    for k in ("identities", "stock"):
        assert out[k] == canonical_source(k, c["expected"][k])
    assert {k: v for k, v in out.items() if k not in ("identities", "stock")} == canonical(PLACE), "place files untouched"
    assert apply(out, invert(c["ops"])) == canonical(files), "every content op has an inverse"


def test_content_ops_need_their_source():
    c = json.loads((STOCK / "content_all.json").read_text())
    with pytest.raises(EditConflict, match="no people source"):
        apply(PLACE, c["ops"][:1])
    with pytest.raises(EditConflict, match="no stock source"):
        apply(PLACE, c["ops"][1:2])


@pytest.mark.parametrize("op", [
    {"n": 1, "op": "identity.edit", "person": {"id": "a"}},                                    # no before
    {"n": 1, "op": "identity.edit", "person": {"id": "a"}, "before": {"id": "b"}},              # another person
    {"n": 1, "op": "stock.container.set", "container": {"ref": "r"}},                            # no space
    {"n": 1, "op": "stock.container.set", "container": None},
    {"n": 1, "op": "stock.possessions.set", "possessions": None, "before": None},
    {"n": 1, "op": "stock.trader.set", "trader": {"person": "a"}},                               # no before
    {"n": 1, "op": "stock.delivery.set", "delivery": {"by": "person"}},                          # no give_seq
    {"n": 1, "op": "stock.loose.edit", "loose": {"id": "a"}, "before": "x"}])
def test_content_op_schema(op):
    from tools.places import edits
    with pytest.raises(EditError):
        edits.check_op(op)


def test_content_save_writes_sources_and_taste_preferences(tmp_path):
    """apply_save then write_place: the place's people and stock sources are written beside the places folder, a
    taste content op is a preference naming what it changed, and an unchanged source is never rewritten."""
    from tools.places import edits
    root = tmp_path / "newworld" / "places" / "fixture"
    src = tmp_path / "newworld" / "sources"
    write_place(root, PLACE)
    (src / "people").mkdir(parents=True)
    (src / "stock" / "places").mkdir(parents=True)
    (src / "people" / "fixture.json").write_text(json.dumps(STOCK_BASE["identities"], indent=1) + "\n")
    stock_text = edits.dump_stock(STOCK_BASE["stock"])
    (src / "stock" / "places" / "fixture.json").write_text(stock_text)
    files = load_place(root)
    assert files["identities"] == edits.canonical_source("identities", STOCK_BASE["identities"])
    assert files["stock"] == edits.canonical_source("stock", STOCK_BASE["stock"])
    ops = json.loads((STOCK / "content_all.json").read_text())["ops"][:2]
    ops[1]["call"] = "taste"
    out = apply_save(files, {"save_id": "s1", "place_id": "fixture", "ops": ops})
    write_place(root, out)
    assert json.loads((src / "people" / "fixture.json").read_text())["people"][0]["name"] == "Ada Hot-Hand"
    text = (src / "stock" / "places" / "fixture.json").read_text()
    assert text != stock_text and '\n  {"ref": "fixture.chest1"' in text, "one row per line, as the source is kept"
    assert out["place"]["preferences"][-1]["what"] == "House/fixture.chest1"
    again = load_place(root)
    assert again["identities"] == out["identities"] and again["stock"] == out["stock"]
    # a save with no content op leaves both sources exactly as their author wrote them
    (src / "people" / "fixture.json").write_text(json.dumps(out["identities"], indent=2))
    layout = (src / "people" / "fixture.json").read_text()
    write_place(root, load_place(root))
    assert (src / "people" / "fixture.json").read_text() == layout


@pytest.mark.skipif(not (HELSTROM.parent.parent / "sources/people/helstrom.json").exists(), reason="no people source")
def test_real_helstrom_identity_and_stock_ops():
    files = load_place(HELSTROM)
    assert files.get("identities") and files.get("stock") is not None
    p0 = files["identities"]["people"][0]
    p1 = copy.deepcopy(p0) | {"name": p0["name"] + " Test", "wealth": "W4"}
    c = {"ref": "helstrom.TESTCHEST", "space": "exterior", "kind": "chest", "security": "S1", "tier": "T1", "gold": 5,
         "items": [], "why": "a test", "cites": []}
    had = next((x for x in files["stock"].get("possessions", []) if x["person"] == p0["id"]), None)
    ops = [{"n": 1, "op": "identity.edit", "person": p1, "before": p0},
           {"n": 2, "op": "stock.container.set", "container": c},
           {"n": 3, "op": "stock.possessions.set", "possessions": {"person": p0["id"], "items": [], "why": "t"},
            "before": had}]
    out = apply(files, ops)
    assert apply(out, invert(ops)) == canonical(files)
