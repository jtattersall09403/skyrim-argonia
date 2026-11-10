"""A copied room is the cell as the game shows it (every holder of the source's load order, the winner per ref), the
rooms check proves it against the bundle, and a guard's issue follows the scale's rule."""
import json

from tools.places import build as B
from tools.places import check as K
from tools.places.stock import split

MASTERS = {"Skyrim.esm": [], "Update.esm": ["Skyrim.esm"], "Dawnguard.esm": ["Skyrim.esm", "Update.esm"],
           "Black Marsh.esm": ["Skyrim.esm", "Update.esm", "Dawnguard.esm"], "Black Marsh North.esp": ["Skyrim.esm", "Black Marsh.esm"]}


def test_a_cell_is_held_by_its_origin_and_every_plugin_mastering_it_in_load_order(monkeypatch):
    monkeypatch.setattr(B, "source_names", lambda p: MASTERS[p] + [p])
    order = list(MASTERS)
    assert B.cell_holders(order, "Dawnguard.esm:000811") == ["Dawnguard.esm", "Black Marsh.esm"]
    assert B.cell_holders(order, "Black Marsh.esm:0AA665") == ["Black Marsh.esm", "Black Marsh North.esp"]


def test_a_copied_room_is_every_holders_refs_with_the_last_holders_version_winning(monkeypatch, tmp_path):
    held = {
        "Dawnguard.esm": {"fk": "Dawnguard.esm:000811", "name": "Jail", "refs": [
            {"fk": "Dawnguard.esm:000A01", "base": "Skyrim.esm:0001AA", "base_type": "LIGH", "pos": [0, 0, 0], "rot": [0, 0, 0]},
            {"fk": "Dawnguard.esm:000A02", "base": "Skyrim.esm:0002BB", "base_type": "STAT", "pos": [1, 0, 0], "rot": [0, 0, 0]},
            {"fk": "Dawnguard.esm:000A03", "base": "Skyrim.esm:0002BB", "base_type": "STAT", "pos": [2, 0, 0], "rot": [0, 0, 0]}],
            "navmesh": [{"fk": "Dawnguard.esm:000B01"}]},
        "Black Marsh.esm": {"fk": "Dawnguard.esm:000811", "name": "Jail", "refs": [
            {"fk": "Dawnguard.esm:000A02", "base": "Skyrim.esm:0002BB", "base_type": "STAT", "pos": [9, 9, 9], "rot": [0, 0, 0]},
            {"fk": "Dawnguard.esm:000A03", "base": "Skyrim.esm:0002BB", "base_type": "STAT", "deleted": True},
            {"fk": "Black Marsh.esm:000C01", "base": "Skyrim.esm:0003CC", "base_type": "LIGH", "pos": [3, 0, 0], "rot": [0, 0, 0]}],
            "navmesh": []},
    }
    monkeypatch.setattr(B, "resolve_copy", lambda c: ("Dawnguard.esm|Black Marsh.esm", "Dawnguard.esm:000811"))
    monkeypatch.setattr(B, "source_cell", lambda pl, cell, out: held.get(pl))

    class Ids:
        def __call__(self, key):
            return f"{B.PLUGIN}:{abs(hash(key)) % 0xFFFFFF:06X}"
    P = {"place": {}, "spaces": {"jail": {"space": {"copy_of": "src/jail"}, "refs": []}}}
    S = B.plan_spaces(P, Ids(), tmp_path)
    rows = {r["src"]: r for r in S["refs"]}
    assert set(rows) == {"Dawnguard.esm:000A01", "Dawnguard.esm:000A02", "Black Marsh.esm:000C01"}
    assert rows["Dawnguard.esm:000A02"]["pos"] == [9, 9, 9]  # the later holder's version
    I = S["interiors"][0]
    assert I["src_plugins"] == ["Dawnguard.esm", "Black Marsh.esm"] and I["copy"]["plugin"] == "Black Marsh.esm"
    assert I["src_navmesh"] == ["Dawnguard.esm:000B01"]


def _bundle(tmp_path, monkeypatch, refs):
    d = tmp_path / "bundles" / "src.s" / "spaces" / "jail"
    d.mkdir(parents=True)
    (d / "refs.jsonl").write_text("".join(json.dumps(r) + "\n" for r in refs))
    monkeypatch.setattr(B, "OUT", tmp_path)


def test_the_rooms_check_names_a_copied_room_built_short_of_its_source(monkeypatch, tmp_path):
    _bundle(tmp_path, monkeypatch, [
        {"id": "Dawnguard.esm:000A01", "kind": "light", "pos": [0, 0, 0]},
        {"id": "Dawnguard.esm:000A02", "kind": "static", "pos": [0, 0, 0]},
        {"id": "Black Marsh.esm:000C01", "kind": "static", "pos": [0, 0, 0]},
        {"id": "Black Marsh.esm:000C02", "kind": "actor", "pos": [0, 0, 0]}])
    plan = {"interiors": [{"space": "jail", "copy": {"plugin": "Black Marsh.esm"}, "copy_of": "s/jail"}],
            "refs": [{"fk": "P:01", "space": "jail", "src": "Black Marsh.esm:000C01"}]}
    ctx = {"plan": plan, "place_dir": tmp_path / "place", "dump": {"refs": [{"fk": "P:01", "base_type": "STAT"}], "actors": [], "npcs": []}}
    bad = K.check_rooms(ctx)
    assert len(bad) == 1 and "built 1 refs, 0 lights" in bad[0] and "3 refs, 1 lights" in bad[0] and "Dawnguard.esm" in bad[0]
    plan["refs"] += [{"fk": "P:02", "space": "jail", "src": "Dawnguard.esm:000A01"}, {"fk": "P:03", "space": "jail", "src": "Dawnguard.esm:000A02"}]
    ctx["dump"]["refs"] += [{"fk": "P:02", "base_type": "LIGH"}, {"fk": "P:03", "base_type": "STAT"}]
    assert K.check_rooms(ctx) == []


def test_a_ref_the_place_removes_is_not_owed_by_the_room(monkeypatch, tmp_path):
    _bundle(tmp_path, monkeypatch, [{"id": "Dawnguard.esm:000A02", "kind": "static", "pos": [0, 0, 0]}])
    sp = tmp_path / "place" / "spaces" / "jail"
    sp.mkdir(parents=True)
    (sp / "refs.jsonl").write_text(json.dumps({"id": "x", "src": "Dawnguard.esm:000A02", "removed": True}) + "\n")
    plan = {"interiors": [{"space": "jail", "copy": {"plugin": "Black Marsh.esm"}, "copy_of": "s/jail"}], "refs": []}
    assert K.check_rooms({"plan": plan, "place_dir": tmp_path / "place", "dump": {"refs": [], "actors": [], "npcs": []}}) == []


def test_a_capitals_guards_wear_their_cultures_set_and_a_poor_places_the_plain_issue():
    plugins = ["Skyrim.esm", "Black Marsh.esm", "Black Marsh North.esp"]
    got = split.guard_issue("forest-green", "T4", plugins)
    assert got["set"]["id"] == "argonian" and got["tier"] == "T3" and got["torch"] == "Skyrim.esm:01D4EC"
    assert split.guard_issue("forest-green", "T2", plugins)["set"] is None  # the band does not reach the set's tier
    assert split.guard_issue("forest-green", "T4", ["Skyrim.esm"])["set"] is None  # the place's mods do not provide it
    assert split.guard_issue("forest-green", "T2", plugins)["tier"] == "T2"
