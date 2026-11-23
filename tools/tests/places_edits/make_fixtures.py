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

DOOR_OUT = dict(ref("30", "0D7030", "door", (1800, 2000, 60)),
                door={"to_space": "FixHouse02", "to_ref": "fix.31", "to_pos": [0, -100, 0], "to_rot": [0, 0, 0]})
DOOR_IN = dict(ref("31", "0D7031", "door", (0, -100, 0), mode="free"),
               door={"to_space": "exterior", "to_ref": "fix.30", "to_pos": [1800, 2000, 60], "to_rot": [0, 0, 0]})
COPY = [
    {"n": 1, "op": "ref.add", "space": "exterior", "ref": DOOR_OUT},
    {"n": 2, "op": "ref.add", "space": "FixHouse02", "ref": DOOR_IN, "space_copy_of": "bmv.fixture/FixHouse02",
     "space_name": "House"},
    {"n": 3, "op": "ref.add", "space": "FixHouse02", "ref": ref("32", "0D7032", "furniture", (50, 50, 0), mode="free")},
]
DRAFT_ROW = PLACE["clear"][0]
# The owner's walking-mesh zones (walk.jsonl): a block zone, a walk zone moved, a join with a note, one removed.
BLOCK = {"id": "fix.w1", "kind": "block", "space": "exterior", "by": "owner",
         "outline": [[900, 1900, 50], [1100, 1900, 50], [1100, 2100, 50], [900, 2100, 50]]}
WALKZ = {"id": "fix.w2", "kind": "walk", "space": "exterior", "by": "owner",
         "outline": [[1300, 1900, 48], [1500, 1900, 48], [1500, 1980, 60]]}
JOIN = {"id": "fix.w3", "kind": "join", "space": "exterior", "by": "owner", "gap": 256,
        "points": [[1200, 1800, 50], [1260, 1800, 70]]}
WALK = [
    {"n": 1, "op": "walk.add", "space": "exterior", "walk": BLOCK},
    {"n": 2, "op": "walk.add", "space": "exterior", "walk": WALKZ},
    {"n": 3, "op": "walk.add", "space": "exterior", "walk": JOIN},
    {"n": 4, "op": "walk.edit", "space": "exterior", "walk": dict(WALKZ, outline=[[x + 40, y, z] for x, y, z in WALKZ["outline"]]),
     "before": WALKZ},
    {"n": 5, "op": "walk.edit", "space": "exterior", "walk": dict(JOIN, note="the guards should cross here"), "before": JOIN},
    {"n": 6, "op": "walk.remove", "space": "exterior", "walk": BLOCK},
]
# Added cases (round 2): copying an enterable building with its room; a draft clearance row restored whole.
CASES2 = {
    "interior_copy": COPY,
    "veg_restore_draft_row": [{"n": 1, "op": "veg.restore", "space": "exterior", "items": [DRAFT_ROW]}],
    "walk_zones": WALK,
    # raising a thing seated `on` another is its seat's own dz (the pos z is what the seat then works out)
    "seated_raise": [{"n": 1, "op": "ref.move", "space": "exterior", "id": "fix.03", "call": "fault",
                      "before": {"pos": [1010, 2050, 51], "rot": [0, 0, 0], "scale": 0.8, "seat": {"mode": "on", "dz": 0.0}},
                      "after": {"pos": [1010, 2050, 81], "rot": [0, 0, 0], "scale": 0.8, "seat": {"mode": "on", "dz": 30.0}}}],
}
# a unit moved and turned whole: its building, what sits on it, its door with the arrival turned with it, the
# person's spot and the quest spot standing in it, all in one op
UDOOR = dict(ref("30", "0D7030", "door", (1000, 1700, 50)), door={"to_space": "Elsewhere", "to_ref": "x.1", "arrival": [1000, 1600, 50]})
UQ = {"id": "q.fix/thing", "quest": "q.fix", "ref": "thing", "space": "exterior", "pos": [1020, 2010, 60], "rot": [0, 0, 0]}
P1 = PLACE["people"][0]
UBACK = dict(ref("31", "0D7031", "door", (5000, 5000, 0)), door={"to_space": "Elsewhere", "to_ref": "fix.30", "to_pos": [1000, 1610, 50]})
CASES2["unit_move"] = [
    {"n": 1, "op": "ref.add", "space": "exterior", "ref": UDOOR},
    {"n": 2, "op": "ref.add", "space": "exterior", "ref": UBACK},   # leads to the door: its landing shifts as the arrival does
    {"n": 3, "op": "quest.add", "space": "exterior", "quest": UQ},
    {"n": 4, "op": "unit.move", "space": "exterior", "unit": "u.house", "name": "the house", "call": "fault",
     "refs": [{"id": "fix.01", "before": {"pos": [1000, 2000, 50], "rot": [0, 0, 1.57]}, "after": {"pos": [1300, 2000, 50], "rot": [0, 0, 3.14]}},
              {"id": "fix.03", "before": {"pos": [1010, 2050, 51], "rot": [0, 0, 0]}, "after": {"pos": [1350, 1990, 51], "rot": [0, 0, 1.57]}},
              {"id": "fix.30", "before": {"pos": [1000, 1700, 50], "door": UDOOR["door"]},
               "after": {"pos": [1000, 2300, 50], "door": dict(UDOOR["door"], arrival=[1000, 2400, 50])}}],
     "people": [{"person": dict(P1, routine=[dict(P1["routine"][0], at=dict(P1["routine"][0]["at"], pos=[1400, 1900, 50]))]), "before": P1}],
     "quests": [{"quest": dict(UQ, pos=[1290, 2020, 60]), "before": UQ}],
     "walks": [{"walk": dict(WALKZ, outline=[[x + 300, y, z] for x, y, z in WALKZ["outline"]]), "before": WALKZ}],
     # the street ending at its door: the end moves with it, the point before it half as far
     "paths": [{"path": dict(PLACE["paths"][0], points=[[1300, 1900], [1550, 1900]]), "before": PLACE["paths"][0]}]},
]
CASES2["unit_move"].insert(3, {"n": 3, "op": "walk.add", "space": "exterior", "walk": WALKZ})   # a zone at its steps moves with it
for i, o in enumerate(CASES2["unit_move"]):
    o["n"] = i + 1
# a thing put into a unit by hand, another taken out of every unit ("" ), and a third given back to the rule (null)
CASES2["unit_member"] = [
    {"n": 1, "op": "ref.move", "space": "exterior", "id": "fix.02", "before": {"unit": None}, "after": {"unit": "u.house"}},
    {"n": 2, "op": "ref.move", "space": "exterior", "id": "fix.03", "before": {"unit": None}, "after": {"unit": ""}},
    {"n": 3, "op": "ref.move", "space": "exterior", "id": "fix.02", "before": {"unit": "u.house"}, "after": {"unit": None}},
]
CONFLICTS2 = {
    "interior_door_unpaired": ([COPY[0], dict(COPY[1], ref=dict(DOOR_IN, door=dict(DOOR_IN["door"], to_ref="fix.99"))), COPY[2]],
                               "does not lead back"),
    "interior_copy_into_existing": ([dict(COPY[1], space="FixHouse01")], "already exists"),
    "walk_remove_missing": ([dict(WALK[5], n=1)], "does not exist"),
}


def main():
    (HERE / "place.json").write_text(json.dumps(PLACE, indent=1, sort_keys=True) + "\n")
    cases = {"all_ops": {"ops": OPS, "expected": apply(PLACE, OPS)}}
    cases.update({k: {"ops": v, "expected": apply(PLACE, v)} for k, v in CASES2.items()})
    for name, (ops, err) in {**CONFLICTS, **CONFLICTS2}.items():
        try:
            apply(PLACE, ops)
            raise SystemExit(f"{name} applied")
        except EditError:
            cases[name] = {"ops": ops, "error": err}
    for name, c in cases.items():
        (HERE / f"{name}.json").write_text(json.dumps(c, indent=1, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
