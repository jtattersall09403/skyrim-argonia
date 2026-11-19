"""What a place stands and walks on: walkway decks a person can walk (paths.is_deck, walk.walk_base, walk.relay),
added things on ground that carries their whole footprint (adds.ground_ok, adds.settle), and a source site our
record never names left out with its mouth (interiors.unused_rooms, interiors.mouth)."""
import math
from types import SimpleNamespace

from tools.places.draft import adds, interiors, io, paths, walk

BOARD = {"key": "K:board", "edid": "CypressStockadePlanks01", "model": "argonia/stockades/minewoodplanks01.nif",
         "bounds": [[-3, -125, -36], [3, 125, 36]]}
DOCK = {"key": "K:dock", "edid": "MudHutWalkway01", "model": "argonia/mudhuts/tamu_wooddock01.nif",
        "bounds": [[-122, -65, -4], [133, 62, 133]]}
TENT = {"key": "S:tent", "model": "clutter/tent/tentlarge.nif", "bounds": [[-200, -290, 0], [200, 290, 300]]}


class Slope:
    """Ground rising `rise` units per unit east of x0, flat west of it; water west of `shore`."""

    def __init__(self, x0=0.0, rise=0.0, shore=None):
        self.x0, self.rise, self.shore = x0, rise, shore

    def height(self, x, y):
        return max(0.0, x - self.x0) * self.rise

    def water(self, x, y):
        return 10.0 if self.shore is not None and x < self.shore else None


def test_a_board_stood_on_edge_is_no_deck_and_a_dock_is():
    assert not paths.is_deck(BOARD)
    assert paths.is_deck(DOCK)
    assert not paths.is_deck({"model": "architecture/docks/dockstepsdown01.nif", "bounds": [[-258, -150, 0], [257, 157, 190]]})


def test_a_deck_is_laid_along_its_long_side():
    length, turn = paths.deck_run(DOCK)          # long along x: turned a quarter so x lies along the walk
    assert length == 255 - 16 and math.isclose(turn, -math.pi / 2)
    assert paths.deck_run(BOARD)[1] == 0.0


def test_joins_fall_back_to_the_styles_walkway_when_the_place_has_none(monkeypatch):
    monkeypatch.setattr(io, "walkway_base", lambda: DOCK)
    bases = {"K:board": BOARD}
    rows = [{"id": f"b{i}", "base": "K:board", "kind": "building", "src": "X.esp:1"} for i in range(8)]
    assert walk.walk_base(rows, bases) == "K:dock" and "K:dock" in bases


def test_a_bridge_laid_on_a_board_is_laid_again_on_the_deck_at_its_walking_height():
    bases = {"K:board": BOARD, "K:dock": DOCK}
    old = {"id": "p.ABC", "base": "K:board", "kind": "building", "pos": [100.0, 200.0, 50.0], "rot": [0, 0, 0.3],
           "src": None, "walk": 36.0, "seat": {"mode": "stilts", "dz": 4.0}, "why": "carries street 01 over our water"}
    keep = {"id": "p.SRC", "base": "K:board", "kind": "building", "pos": [0, 0, 0], "rot": [0, 0, 0], "src": "X.esp:9"}
    rows = [old, keep]
    assert walk.relay(rows, "K:dock", bases, log=lambda m: None) == 1
    new = [r for r in rows if r["base"] == "K:dock"]
    top = new[0]["walk"]
    assert len(new) == 1 and keep in rows                       # 234 of board is one 239-unit deck; a source piece stays
    for r in new:
        assert math.isclose(r["pos"][2] + top, 86.0, abs_tol=0.01)   # the old walking height
        assert math.isclose(r["seat"]["dz"], 4.0 + 36.0 - top, abs_tol=0.05)
    mid = new[0]["pos"][:2]
    assert math.dist(mid, [100.0, 200.0]) < 0.1 and math.isclose(new[0]["rot"][2], (0.3 - math.pi / 2) % (2 * math.pi), abs_tol=1e-4)


LEDGE = {"key": "K:ledge", "edid": "MorrImpKeepLedgeMid02",
         "model": "tesak1243/mwimperialarchitecture/architecture/keep/exterior/ledges/mwimparchledgemid02.nif",
         "bounds": [[-256, -256, 0], [256, 256, 0]]}


def test_a_keeps_ledge_plate_is_walked_but_never_laid_as_a_gangway():
    bases = {"K:ledge": LEDGE, "K:dock": DOCK}
    rows = [{"id": f"l{i}", "base": "K:ledge", "kind": "building", "src": "X.esp:1"} for i in range(8)]
    rows += [{"id": "d", "base": "K:dock", "kind": "building", "src": "X.esp:2"}]
    assert paths.is_deck(LEDGE) and walk.walk_base(rows, bases) == "K:dock"
    old = {"id": "p.J", "base": "K:ledge", "kind": "building", "pos": [0.0, 0.0, 500.0], "rot": [0, 0, 0], "src": None,
           "walk": 0.0, "seat": {"mode": "stilts", "dz": 0.0}, "why": "joins door p.D to the town"}
    rows.append(old)
    assert walk.relay(rows, "K:dock", bases, log=lambda m: None) == 1
    assert all(r["base"] == "K:dock" for r in rows if not r.get("src"))


def test_a_wall_with_a_stair_in_it_is_no_flight():
    wall = {"model": "keep/exterior/walls/mwimparchwallstairs01.nif", "bounds": [[-256, -132, 0], [256, 132, 1174]]}
    assert walk.flight(wall) is None


def test_a_join_is_never_laid_through_a_wall():
    wall = {"key": "K:wall", "model": "keep/exterior/walls/mwimparchlrgwall02.nif", "kind": "building",
            "bounds": [[-128, -28, -256], [131, 27, 274]]}
    bases = {"K:wall": wall, "K:dock": DOCK}
    w = {"id": "w", "base": "K:wall", "kind": "building", "pos": [200.0, 0.0, 800.0], "rot": [0.0, 0.0, 0.0]}
    assert walk.through((200.0, -200.0, 830.0), (200.0, 200.0, 830.0), [w], bases)        # across it
    assert not walk.through((0.0, -200.0, 830.0), (0.0, 200.0, 830.0), [w], bases)        # beside it
    assert walk.lay("p", "d", [200.0, -200.0, 830.0], [200.0, 200.0, 830.0], "K:dock", [w], bases, None) == []


def test_a_flight_whose_top_tread_is_already_on_the_ground_is_not_hung():
    fl = {"top": 0.0, "foot": 400.0, "us": [0.0, 200.0, 400.0], "zs": [500.0, 250.0, 0.0]}
    flat = Slope()                                       # ground at 0 everywhere
    got, buried = walk.landing(fl, -500.0, (0.0, 0.0), (1.0, 0.0), flat)   # top tread at 0: the deck is on the ground
    assert got is None and buried is None
    got, buried = walk.landing(fl, 0.0, (0.0, 0.0), (1.0, 0.0), flat)      # top at 500: it comes down to its foot
    assert got == (400.0, 0.0, 0.0) and buried == 0.0


def test_a_thing_on_a_slope_or_over_water_has_no_ground_under_it():
    row = {"id": "a", "base": "S:tent", "kind": "building", "pos": [0.0, 0.0, 0.0], "rot": [0, 0, 0],
           "seat": {"mode": "ground", "dz": 0.0, "foot": [-200, -290, 200, 290]}}
    assert adds.ground_ok(row, Slope(x0=10_000), 64.0)
    assert not adds.ground_ok(row, Slope(x0=-200, rise=0.5), 64.0)          # rises 200 under it
    assert not adds.ground_ok(row, Slope(x0=10_000, shore=0.0), 64.0)        # water under its west half


def test_settle_moves_a_tent_onto_ground_that_carries_it_with_its_bed():
    bases = {"S:tent": TENT, "S:bed": {"model": "furniture/bedroll.nif", "bounds": [[-40, -90, 0], [40, 90, 20]]}}
    tent = {"id": "t", "base": "S:tent", "kind": "building", "pos": [0.0, 0.0, 0.0], "rot": [0, 0, 0],
            "seat": {"mode": "ground", "dz": 0.0, "foot": [-200, -290, 200, 290]}}
    bed = {"id": "b", "base": "S:bed", "kind": "furniture", "pos": [50.0, 0.0, 0.0], "rot": [0, 0, 0],
           "seat": {"mode": "ground", "dz": 0.0, "foot": [-40, -90, 40, 90]}}
    G = Slope(x0=-100, rise=1.0)                                # flat west of x = -100
    assert adds.settle([tent, bed], [], bases, G, 64.0, log=lambda m: None) == 1
    assert adds.ground_ok(tent, G, 64.0)
    assert math.isclose(bed["pos"][0] - tent["pos"][0], 50.0) and bed["pos"][1] == tent["pos"][1]


def _bundle():
    door = {"id": "S:mdoor", "kind": "door", "pos": [0, 0, 0], "door": {"to_space": "DushnikhYalMine"}}
    home = {"id": "S:hdoor", "kind": "door", "pos": [3000, 0, 0], "door": {"to_space": "DushnikhYalLonghouse"}}
    rock = {"id": "S:rock", "kind": "rock", "pos": [100, 0, 0]}
    cart = {"id": "S:cart", "kind": "clutter", "pos": [300, 50, 0]}
    hall = {"id": "S:hall", "kind": "building", "pos": [2900, 0, 0]}
    spaces = {"DushnikhYalMine": SimpleNamespace(meta={"name": None}),
              "DushnikhYalLonghouse": SimpleNamespace(meta={"name": "Longhouse"})}
    cl = [SimpleNamespace(id="b01", members=["S:hdoor", "S:hall", "S:mdoor"]),
          SimpleNamespace(id="s01", members=["S:rock", "S:cart"])]
    refs = [door, home, rock, cart, hall]
    return SimpleNamespace(spaces=spaces), refs, cl, {"S:mdoor": "b01", "S:hdoor": "b01", "S:hall": "b01",
                                                      "S:rock": "s01", "S:cart": "s01"}


def test_a_mine_the_record_never_names_goes_with_its_door_and_mouth():
    src, refs, cl, of = _bundle()
    by = {r["id"]: r for r in refs}
    doors = [r for r in refs if r["kind"] == "door"]
    got = interiors.unused_rooms(src, doors, "a naga camp with a longhouse where the guards keep their pay")
    assert list(got) == ["S:mdoor"] and "mine" in got["S:mdoor"]
    assert interiors.mouth(by["S:mdoor"], cl, of, by) == {"S:mdoor", "S:rock", "S:cart"}
    assert interiors.unused_rooms(src, doors, "the old mine under the camp") == {}


def test_a_gate_is_walked_through_and_a_load_door_or_a_wall_is_not():
    from tools.places import build
    assert build.walked_through({"kind": "door", "base": "Skyrim.esm:01AE14"})
    assert not build.walked_through({"kind": "door", "base": "Skyrim.esm:027FE8", "door": {"to_space": "Longhouse"}})
    assert not build.walked_through({"kind": "building", "base": "Skyrim.esm:0349A8"})
