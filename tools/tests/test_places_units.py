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


def test_a_join_given_up_for_a_flight_is_measured_but_not_flagged():
    pl = place({"s.walk": -300.0})
    assert [j["flag"] for j in U.joins(pl) if j["flag"]]                      # both ends of the lowered walkway
    pl.sc.files["place"]["draft"] = {"joins_given_up": [{"walk": "house.RoomA", "unit": "walkway.01", "why": "a flight"}]}
    js = {j["unit"]: j for j in U.joins(pl)}
    assert js["house.RoomA"]["flag"] is None and js["house.RoomA"]["given_up"] == "a flight"
    assert js["house.RoomB"]["flag"]                                          # the other end is still a fault


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


def test_units_apply_writes_the_plan_as_moves_that_put_a_house_back_together_and_trees_back_on_the_ground(tmp_path):
    pl = place({"s.huta": -120.0, "s.tree": -300.0}, ground_h=100.0)
    ed = tmp_path / "t" / "agent-edits"
    ed.mkdir(parents=True)
    (ed / "a.json").write_text(json.dumps({"ops": [   # an earlier stroke sank the house and dragged the tree with it
        {"op": "ref.move", "space": "exterior", "id": "d.huta", "stroke": 1, "before": {"pos": [0, 0, 500]}, "after": {"pos": [0, 0, 380]}},
        {"op": "ref.move", "space": "exterior", "id": "d.tree", "stroke": 1, "before": {"pos": [450, 0, 0]}, "after": {"pos": [450, 0, -300]}}]}))
    p = U.plan(pl)
    strokes, report = U.apply_strokes(pl, p, ["house.RoomA"], places=tmp_path, files=pl.sc.files)
    after = {op["id"]: op["after"]["pos"][2] for st in strokes for op in st}
    dz = {u["unit"]: u for u in p["units"]}["house.RoomA"]["dz"]
    plat = after.get("d.plata", 500.0)
    assert after["d.huta"] - plat == pytest.approx(0.0)                     # the body back on its deck, as in the source
    assert plat == pytest.approx(500.0 + dz)                                # the whole house took the plan's one offset
    assert after["d.tree"] == pytest.approx(0.0)                           # the tree back where the ground puts it
    assert "d.platb" not in after                                          # a unit not named is not touched
    assert len(strokes) == 2 and all(op["op"] == "ref.move" for op in strokes[-1])


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
    assert len(bad) == 1 and "d.tree" in bad[0] and "-340" in bad[0]
    # a later stroke of the ground alone that puts it back (units apply's restore) clears it
    (ed / "b.json").write_text(json.dumps({"ops": [mv("d.tree", 340, 1)]}))
    assert U.edit_faults(files, BASES, tmp_path) == []


def test_a_placed_piece_keeps_its_height_through_any_later_seating():
    from tools.places.seat import pin, seat_all
    G = flat(100.0)
    deck = {"id": "deck", "pos": [0, 0, 400.0], "rot": [0, 0, 0], "seat": {"mode": "ground", "dz": 0.0}}
    hut = {"id": "hut", "pos": [0, 0, 650.0], "rot": [0, 0, 0], "seat": {"mode": "on", "on": "deck", "dz": 0.0}}
    deck["seat"] = pin(deck, 400.0, G, {})
    hut["seat"] = pin(hut, 650.0, G, {"deck": deck})
    assert deck["seat"]["dz"] == 300.0 and hut["seat"]["dz"] == 250.0
    assert seat_all([hut, deck], G) == 0 and hut["pos"][2] == 650.0
    free = {"id": "f", "pos": [0, 0, 5.0], "seat": {"mode": "free"}}
    assert pin(free, 50.0, G) == {"mode": "free"}


def test_what_lay_on_the_source_ground_by_a_house_lies_on_ours():
    from tools.places import xform
    G = flat(0.0)

    def piece(z):
        return {"lo": [-20, -20, 0], "hi": [20, 20, 40], "m": xform.matrix([0, 0, z], [0, 0, 0], 1)}
    assert U._on_src_ground(piece(20.0), G) == pytest.approx(20.0)                  # on the ground
    assert U._on_src_ground(piece(300.0), G) is None                                # on the deck
    assert U._on_src_ground(piece(150.0), G, stand=500.0) == pytest.approx(150.0)   # a fire pit under the deck
    assert U._on_src_ground(piece(480.0), G, stand=500.0) is None                   # on the deck


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


def test_draft_check_refuses_a_house_moved_apart_from_its_platform(tmp_path: Path):
    bad = U.check_faults("t", tmp_path, place({"s.huta": -120.0}))
    assert len(bad) == 1 and bad[0].startswith("house.RoomA: a house moved apart from its platform")
    assert U.check_faults("t", tmp_path, place({"s.huta": -4.0})) == []


def test_the_hands_act_on_a_unit_and_refuse_a_body_without_its_deck():
    from tools.places.look import hands
    pl = place({})
    sc = pl.sc
    sc.place_id, sc._units = "t", pl
    sc._of = lambda name, kind, pieces: {"name": name, "kind": kind, "pieces": pieces}
    sc.resolve = lambda name: sc._of(name, "piece", [sc.by_id[name]])
    th = hands.thing(sc, "house.RoomA")
    assert th["kind"] == "unit" and {"d.huta", "d.plata", "d.doora", "d.lampa"} <= {p["id"] for p in th["pieces"]}
    with pytest.raises(ValueError, match="moves with its platform"):
        hands.thing(sc, "d.huta")
    assert hands.thing(sc, "d.huta", piece=True)["pieces"][0]["id"] == "d.huta"
    assert hands.thing(sc, "d.tree")["pieces"][0]["id"] == "d.tree"


HIST_BASES = {
    "hist": {"edid": "ArgoniaTreeHist01", "kind": "tree", "model": "t/histtree01.nif", "bounds": [[-900, -900, -100], [900, 900, 1600]]},
    "swap": {"edid": "HistTree01", "kind": "static", "model": "t/histtree01.nif", "bounds": [[-900, -900, -100], [900, 900, 1600]]},
    "root": {"edid": "HistRoot03", "kind": "tree", "model": "t/histroot03.nif", "bounds": [[-60, -340, -130], [90, 120, 540]]},
    "gland": {"edid": "HistGland03", "kind": "tree", "model": "t/histgland03.nif", "bounds": [[-100, -100, -270], [100, 100, 300]]},
    "vine": {"edid": "HistMossyVinesFloor01", "kind": "plant", "model": "t/histmossyvinesfloor01.nif", "bounds": [[-210, -240, -15], [260, 260, 10]]},
    "sap": {"edid": "WaterPuddleHist", "kind": "activator", "model": "water/waterpuddle01.nif", "bounds": [[-150, -150, 0], [150, 200, 0]]},
}


def test_a_hist_is_one_unit_with_its_roots_glands_and_sap_and_is_seated_by_its_own_rule():
    """A Hist the draft swapped for another base is found where the source's stood; what hung on the source's tree goes
    back to its height on the trunk, a root that stood on the source's ground is sunk until its foot is in ours."""
    bases = {**BASES, **HIST_BASES}
    src = [row("s.hist", "plat", 0, 0, 700), row("s.root", "plat", 1000, 0, 300), row("s.gland", "plat", 300, 0, 1300),
           row("s.vine", "plat", 2000, 0, 1500)]
    for r, b in zip(src, ("hist", "root", "gland", "vine")):
        r["base"], r["kind"] = b, HIST_BASES[b]["kind"]
    # our ground is flat at 500 (the source's mound gone): the trunk stands lower against the gland, the root hangs
    rows = [dict(row("d.trunk", "plat", 50, 0, 600), base="swap", kind="static", src=None),
            dict(row("d.root", "plat", 1050, 0, 700), base="root", kind="tree", src="s.root"),
            dict(row("d.gland", "plat", 350, 0, 1300), base="gland", kind="tree", src="s.gland"),
            dict(row("d.sap", "plat", 50, 0, 500), base="sap", kind="activator", src=None)]

    def bnd(b):
        return (b.get("bounds") or [[-32, -32, 0], [32, 32, 64]]), True

    class Sc(FakeScene):
        def __init__(self):
            self.bases, self.ground, self.space = bases, flat(500.0), "exterior"
            self.refs = {r["id"]: r for r in rows}
            self.pieces = U.pieces_of(rows, bases, bnd)
            self.by_id = {p["id"]: p for p in self.pieces}
            self.files = {"place": {"place_id": "t", "source_id": "t"}, "spaces": {"exterior": {"refs": rows}}}
    src_ground = Ground({(c, d): [300.0] * 33 * 33 for c in range(-2, 2) for d in range(-2, 2)}, {}, None)
    pl = U.Place.of("t", Sc(), U.pieces_of(src, bases, bnd), src_ground)
    hist = [u for u in pl.units if u["kind"] == "hist"]
    assert len(hist) == 1, [u["id"] for u in pl.units]
    un = hist[0]
    assert un["pieces"]["trunk"] == ["d.trunk"] and un["pieces"]["sap"] == ["d.sap"]
    assert un["pieces"]["root"] == ["d.root"] and un["pieces"]["gland"] == ["d.gland"]
    assert "s.vine" not in [i for v in pl.src_units[0]["pieces"].values() for i in v]   # too far from the trunk
    m = U.measure(pl, un)
    assert any("root HistRoot03" in f and "hangs" in f for f in m["flags"]), m["flags"]
    assert any("gland HistGland03" in f and "off its place on the trunk (+100)" in f for f in m["flags"]), m["flags"]
    assert not any("floor" in f for f in m["flags"])
    dz = U.hist_reassembly(pl, un)
    assert dz["d.gland"] == -100.0                  # back at the source's 600 over the trunk
    assert dz["d.root"] == -(70.0 + U.BURY_MIN)     # its foot (570) sunk BURY_MIN into our ground


def test_a_huts_light_is_a_fixture_not_a_house():
    lamp = {"id": "l", "kind": "building", "model": "vvardenfell/ashlanderhut/allight05.nif"}
    hut = {"id": "h", "kind": "building", "model": "vvardenfell/ashlanderhut/ashlanderhut01.nif"}
    assert U._role0(lamp) != "body" and U._role0(hut) == "body"
    rope = {"id": "r", "kind": "building", "model": "clutter/ruins/ruinsceilingropeshort.nif"}
    assert U._role0(lamp) == "loose" and U._role0(rope) == "loose"
