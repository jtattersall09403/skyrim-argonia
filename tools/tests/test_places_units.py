"""A place's units (tools/places/units.py): a house is its body with its own platform, posts, door and what hangs on
it; a walkway names what its ends rest on; trees stay with the ground. Measured on our ground and planned as wholes."""
import json
from pathlib import Path

import pytest

from tools.places import units as U
from tools.places.seat import Ground

BASES = {
    "plat": {"edid": "MurkmirePlatformBase02", "kind": "building", "model": "t/house04platform.nif",
             "bounds": [[-400, -300, -520], [400, 300, 0]]},
    "hut": {"edid": "MurkmireThatchHouse06", "kind": "building", "model": "t/thatchhouse06.nif",
            "bounds": [[-300, -250, 0], [300, 250, 450]]},
    "door": {"edid": "ThatchHutDoor01", "kind": "door", "model": "t/shackdoor.nif", "bounds": [[-50, -10, 0], [50, 10, 150]]},
    "lamp": {"edid": "RopeLantern01", "kind": "static", "model": "t/lantern01.nif", "bounds": [[-10, -10, -30], [10, 10, 30]]},
    "walk": {"edid": "MurkmireWalkwayLong01", "kind": "static", "model": "t/walkway01.nif", "bounds": [[-150, -350, -20], [150, 350, 0]]},
    "tree": {"edid": "ArgoniaTreeJungle08", "kind": "tree", "model": "t/treejungle08.nif", "bounds": [[-60, -60, 0], [60, 60, 2000]]},
    "pot": {"edid": "ALPAPot01", "kind": "clutter", "model": "t/pot01.nif", "bounds": [[-20, -20, 0], [20, 20, 40]]},
}


def bounds(b):
    return (b.get("bounds") or [[-32, -32, 0], [32, 32, 64]]), True


def flat(h=0.0):
    return Ground({(c, d): [h] * 33 * 33 for c in range(-2, 2) for d in range(-2, 2)}, {}, None)


def row(i, base, x, y, z, **kw):
    return {"id": i, "base": base, "kind": BASES[base]["kind"], "pos": [x, y, z], "rot": [0, 0, 0], "scale": 1, **kw}


def town(dy=0.0, prefix="s"):
    """Two stilt huts 1300 apart, a walkway between their platforms, a lantern on a wall, a pot on a deck, a tree."""
    out = []
    for n, y in (("a", 0.0), ("b", -1300.0)):
        out += [row(f"{prefix}.plat{n}", "plat", 0, y, 500), row(f"{prefix}.hut{n}", "hut", 0, y, 500),
                row(f"{prefix}.door{n}", "door", 0, y - 260, 500, door={"to_space": f"Room{n.upper()}"}),
                row(f"{prefix}.lamp{n}", "lamp", 312, y, 800), row(f"{prefix}.pot{n}", "pot", 350, y + 270, 500)]
    out += [row(f"{prefix}.walk", "walk", 0, -650, 500), row(f"{prefix}.tree", "tree", 450, 0, 0)]
    return out


def derive(rows, ground=None):
    return U.derive(U.pieces_of(rows, BASES, bounds), ground or flat(), BASES)


def test_a_house_is_its_body_with_its_own_platform_door_and_hangings_and_a_walkway_names_its_ends():
    us = {u["id"]: u for u in derive(town())}
    a, b = us["house.RoomA"], us["house.RoomB"]
    assert a["pieces"]["body"] == ["s.huta"] and a["pieces"]["deck"] == ["s.plata"]
    assert a["pieces"]["door"] == ["s.doora"] and a["interior"] == "RoomA"
    assert "s.lampa" in a["pieces"]["hanging"] and "s.pota" in a["pieces"]["on"]
    assert b["pieces"]["deck"] == ["s.platb"]
    walks = [u for u in us.values() if u["kind"] == "walkway"]
    assert len(walks) == 1 and sorted(j["unit"] for j in walks[0]["joins"]) == ["house.RoomA", "house.RoomB"]
    # the tree belongs to the ground, never to the house it stands beside
    assert not any("s.tree" in v for u in us.values() for v in u["pieces"].values())


class FakeScene:
    """What units.Place reads of the look tool's scene: pieces, refs, by_id, bases, ground, files."""
    def __init__(self, rows, ground):
        self.bases, self.ground, self.space = BASES, ground, "exterior"
        self.refs = {r["id"]: r for r in rows}
        self.pieces = U.pieces_of(rows, BASES, bounds)
        self.by_id = {p["id"]: p for p in self.pieces}
        self.files = {"place": {"place_id": "t", "source_id": "t"}, "spaces": {"exterior": {"refs": rows}}}

    def everything(self):
        return self.pieces


def draft(moves: dict[str, float], z0=0.0):
    """Our draft of the town: each source row by its src, lifted by z0, with some pieces moved up or down."""
    rows = []
    for r in town():
        d = dict(r, id=r["id"].replace("s.", "d."), src=r["id"])
        d["pos"] = [r["pos"][0], r["pos"][1], r["pos"][2] + z0 + moves.get(r["id"], 0.0)]
        rows.append(d)
    return rows


def place(moves, ground_h=0.0, z0=0.0):
    sc = FakeScene(draft(moves, z0), flat(ground_h))
    return U.Place.of("t", sc, U.pieces_of(town(), BASES, bounds), flat())


def test_a_house_pushed_down_through_its_platform_is_measured_and_flagged():
    pl = place({"s.huta": -120.0, "s.doora": 0.0})
    m = U.measure(pl, pl.unit("house.RoomA"))
    assert m["body_gap"] == pytest.approx(-120) and m["body_gap_src"] == pytest.approx(0)
    assert any("body through its deck" in f for f in m["flags"])
    assert any("door sill off its floor" in f for f in m["flags"])
    ok = U.measure(pl, pl.unit("house.RoomB"))
    assert not ok["flags"], ok["flags"]
    # each foot: the platform's bottom 20 in the ground under it, its leg the source's 520
    assert {f["leg"] for f in ok["feet"]} == {520.0} and min(f["depth"] for f in ok["feet"]) == pytest.approx(20)


def test_the_plan_puts_a_house_back_on_its_platform_and_seats_both_with_the_walkway_level():
    pl = place({"s.huta": -120.0}, ground_h=100.0)   # our ground 100 up: both platforms' feet in it by 80
    p = U.plan(pl)
    by = {u["unit"]: u for u in p["units"]}
    assert by["house.RoomA"]["reassemble"] == {"d.huta": 120.0}
    for h in ("house.RoomA", "house.RoomB"):
        assert not by[h].get("after"), by[h]
        assert by[h]["dz"] is not None and by[h]["window"][0] <= by[h]["dz"] <= by[h]["window"][1]
    walk = next(u for u in p["units"] if u["kind"] == "walkway")
    assert abs(walk["dz"] - by["house.RoomA"]["dz"]) <= U.STEP and not walk.get("give_up")


def test_a_house_on_ground_too_steep_for_its_legs_is_said_so():
    pl = place({}, ground_h=0.0)
    pl.sc.ground = Ground({(c, d): [0.0 if c < 0 else 600.0] * 33 * 33 for c in range(-2, 2) for d in range(-2, 2)}, {}, None)
    # the huts straddle x = 0, where the ground steps 600: no one offset keeps the deck up and every leg in the ground
    r = {u["unit"]: u for u in U.plan(pl, scan=0.0)["units"]}["house.RoomA"]
    assert r["dz"] is None and r["closest"]["short"] > 0


def test_a_tree_moved_in_the_stroke_of_a_building_is_refused(tmp_path: Path):
    rows = draft({})
    files = {"place": {"place_id": "t", "source_id": "t"}, "spaces": {"exterior": {"refs": rows}}}
    ed = tmp_path / "t" / "agent-edits"
    ed.mkdir(parents=True)
    mv = lambda i, dz, s: {"op": "ref.move", "space": "exterior", "id": i, "stroke": s,  # noqa: E731
                           "before": {"pos": [0, 0, 0]}, "after": {"pos": [0, 0, dz]}}
    (ed / "a.json").write_text(json.dumps({"ops": [mv("d.huta", -300, 1), mv("d.tree", -300, 1), mv("d.tree", -40, 2)]}))
    bad = U.edit_faults(files, BASES, tmp_path)
    assert len(bad) == 1 and "d.tree" in bad[0] and "stroke 1" in bad[0]


SEEKHAT = Path(__file__).resolve().parents[2] / "out" / "places" / "bundles" / "src.kingofthemurkmire.seekhatyollocation"


@pytest.mark.skipif(not SEEKHAT.is_dir(), reason="Seekhat Yol's bundle is not extracted here")
def test_seekhat_yol_has_seven_houses_each_with_its_platform_and_named_walkways_between_them():
    from tools.places.draft import io
    from tools.places.look.scene import data_out
    src = io.load(SEEKHAT.name, SEEKHAT.parent)
    bases = {b["key"]: b for b in (json.loads(x) for x in (SEEKHAT / "bases.jsonl").read_text().splitlines() if x.strip())}
    us = U.derive(U.pieces_of(src.exterior.refs, bases, U.footprint_bounds(data_out())), src.ground, bases)
    houses = [u for u in us if u["kind"] == "house"]
    assert len(houses) == 7
    for h in houses:
        assert h["interior"] and h["pieces"].get("deck") and h["pieces"].get("door"), h["id"]
    # most stand on a platform piece; a stilt house on its own legs has a plank floor
    assert sum(any("Platform" in (bases[p["base"]].get("edid") or "") for p in src.exterior.refs
                   if p["id"] in h["pieces"]["deck"]) for h in houses) >= 5
    spans = [u for u in us if u["kind"] in ("walkway", "bridge")]
    two = [u for u in spans if len({j["unit"] for j in u["joins"]}) >= 2]
    assert len(two) >= 5
    assert any({j["unit"] for j in u["joins"]} == {"house.SeekhatFishersHut", "house.SeekhatEldersHut"} for u in spans)
