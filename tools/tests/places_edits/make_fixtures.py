"""Writes the shared fixtures (python tools/tests/places_edits/make_fixtures.py). Lane W's JavaScript mirror reads
the same files: for each case, apply(place, ops) must equal expected, or fail with an error containing error."""
import json
from pathlib import Path

from tools.places.edits import EditError, apply

HERE = Path(__file__).parent
B = "Black Marsh.esm:"


def ref(i, base, kind, pos, rot=(0, 0, 0), scale=1.0, mode="ground"):
    return {"id": f"fix.{i}", "base": B + base, "kind": kind, "pos": list(pos), "rot": list(rot), "scale": scale,
            "layer": "place", "flags": [], "seat": {"mode": mode, "dz": 0.0}, "src": f"bmv.helstrom:{i}"}


PLACE = {
    "place": {"place_id": "fixture", "source_id": "bmv.fixture", "similar": []},
    "spaces": {
        "exterior": {"refs": [ref("01", "0D7001", "building", (1000, 2000, 50), (0, 0, 1.57)),
                              ref("02", "0D7002", "building", (1400, 2000, 48)),
                              ref("03", "0D7003", "clutter", (1010, 2050, 51), scale=0.8, mode="on")],
                     "space": None},
        "FixHouse01": {"refs": [ref("10", "0D7010", "furniture", (10, 20, 0), mode="free")],
                       "space": {"copy_of": "bmv.fixture/FixHouse01"}},
    },
    "clear": [{"base": B + "0A0001", "pos": [990.0, 1990.0, 50.0], "by": "draft"}],
    "land": [{"cell": [3, 7], "verts": [[4, 4, 12.0]], "why": "doorstep"}],
    "paths": [{"id": "fix.path1", "kind": "street", "points": [[1000, 1900], [1400, 1900]], "width": 256,
               "style": "mud"}],
    "people": [{"id": "fix.p1", "name": "Guard 1", "base_from": B + "0E0001", "role": "guard", "home": "fix.01",
                "bed": "fix.10", "work": None, "services": [], "faction_ranks": [],
                "routine": [{"start": 8, "hours": 12, "kind": "patrol", "at": {"space": "exterior", "pos": [1000, 1900, 50], "radius": 256}}],
                "patrol": [[1000, 1900], [1400, 1900]]}],
}

NEW = ref("20", "0D7020", "static", (1200, 2100, 49))
OPS = [
    {"n": 1, "op": "ref.move", "space": "exterior", "id": "fix.01", "call": "fault", "note": "off the bank",
     "before": {"pos": [1000, 2000, 50], "rot": [0, 0, 1.57]}, "after": {"pos": [1000, 1950, 52], "rot": [0, 0, 0]}},
    {"n": 2, "op": "ref.remove", "space": "exterior", "id": "fix.03", "call": "taste", "before": PLACE["spaces"]["exterior"]["refs"][2]},
    {"n": 3, "op": "ref.add", "space": "exterior", "ref": NEW},
    {"n": 4, "op": "veg.clear", "space": "exterior", "items": [{"base": B + "0A0002", "pos": [1395, 1995, 48]}]},
    {"n": 5, "op": "veg.restore", "space": "exterior", "items": [{"base": B + "0A0001", "pos": [990, 1990, 50], "by": "draft"}]},
    {"n": 6, "op": "land.patch", "space": "exterior", "cell": [3, 7], "verts": [[4, 4, 12.0, 0.0], [4, 5, 0.0, -6.5]],
     "tool": {"kind": "lower", "radius": 128, "strength": 0.5}},
    {"n": 7, "op": "path.edit", "space": "exterior", "path": dict(PLACE["paths"][0], width=320), "before": PLACE["paths"][0]},
    {"n": 8, "op": "path.add", "space": "exterior", "path": {"id": "fix.path2", "kind": "path", "points": [[1400, 1900], [1400, 2200]], "width": 128, "style": "mud"}},
    {"n": 9, "op": "person.edit", "space": "exterior", "person": dict(PLACE["people"][0], patrol=[[1000, 1900], [1200, 1800], [1400, 1900]]),
     "before": PLACE["people"][0]},
    {"n": 10, "op": "ref.move", "space": "FixHouse01", "id": "fix.10", "before": {"pos": [10, 20, 0]}, "after": {"pos": [40, 20, 0]}},
]
CONFLICTS = {
    "move_before_mismatch": ([dict(OPS[0], before={"pos": [999, 2000, 50], "rot": [0, 0, 1.57]})], "differs|expected"),
    "add_existing": ([{"n": 1, "op": "ref.add", "space": "exterior", "ref": PLACE["spaces"]["exterior"]["refs"][0]}], "already exists"),
    "remove_missing": ([{"n": 1, "op": "ref.remove", "space": "exterior", "id": "fix.99", "before": NEW}], "is not in"),
    "restore_uncleared": ([{"n": 1, "op": "veg.restore", "space": "exterior", "items": [{"base": B + "0A0009", "pos": [0, 0, 0]}]}], "is not cleared"),
    "land_before_mismatch": ([{"n": 1, "op": "land.patch", "space": "exterior", "cell": [3, 7], "verts": [[4, 4, 0.0, 5.0]]}], "expected"),
    "unknown_op": ([{"n": 1, "op": "ref.paint", "space": "exterior"}], "unknown op"),
}


def main():
    (HERE / "place.json").write_text(json.dumps(PLACE, indent=1, sort_keys=True) + "\n")
    cases = {"all_ops": {"ops": OPS, "expected": apply(PLACE, OPS)}}
    for name, (ops, err) in CONFLICTS.items():
        try:
            apply(PLACE, ops)
            raise SystemExit(f"{name} applied")
        except EditError:
            cases[name] = {"ops": ops, "error": err}
    for name, c in cases.items():
        (HERE / f"{name}.json").write_text(json.dumps(c, indent=1, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
