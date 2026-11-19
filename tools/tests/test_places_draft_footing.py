"""Where people walk and stand: flat floor plates walked as decks (paths.is_plate, walk.deck_heights), work spots
with footing (jail.footing, jail.dry_spot), walkways over water deeper than a wade (bridges), the place's own station
outdoors before one in a room (stages.outdoor_station) and stops on a deck written with their height (Walkable.stood)."""
from types import SimpleNamespace

from tools.places.check import WADE
from tools.places.draft import bridges, jail, walk
from tools.places.draft import paths as P
from tools.places.draft import stages

LEDGE = {"key": "M:ledge", "model": "keep/exterior/ledges/mwimparchledgemid02.nif", "bounds": [[-256, -256, 0], [256, 256, 0]]}
RUG = {"key": "M:rug", "model": "clutter/rug01.nif", "bounds": [[-60, -90, 0], [60, 90, 2]]}
WALL = {"key": "M:wall", "model": "keep/exterior/walls/wall01.nif", "bounds": [[-256, -16, 0], [256, 16, 512]]}
STAIR = {"key": "M:stair", "model": "keep/exterior/ledges/ledgestairs01.nif", "bounds": [[-256, -256, 0], [256, 256, 0]]}


def test_a_flat_wide_plate_is_walked_as_a_deck_and_a_rug_a_wall_or_a_flight_is_not():
    assert P.is_plate(LEDGE) and P.walked(LEDGE) and P.is_deck(LEDGE)
    assert not P.is_plate(RUG) and not P.walked(RUG)
    assert not P.is_plate(WALL) and not P.walked(WALL)
    assert not P.is_plate(STAIR) and P.walked(STAIR) and not P.is_deck(STAIR)


def test_deck_heights_gives_each_walked_piece_its_deck_once(monkeypatch):
    monkeypatch.setattr(walk, "geom_walk", lambda b: 0.0 if P.walked(b) else None)
    rows = [{"id": "a", "base": "M:ledge"}, {"id": "b", "base": "M:wall"}, {"id": "c", "base": "M:ledge", "walk": 12.0}]
    assert walk.deck_heights(rows, {"M:ledge": LEDGE, "M:wall": WALL}) == 1
    assert rows[0]["walk"] == 0.0 and "walk" not in rows[1] and rows[2]["walk"] == 12.0


class Bank:
    """Water at 0; dry land (z 20) for x >= 0, a ford (z -30) for -500 <= x < 0, deep water (z -200) beyond."""
    def height(self, x, y):
        return 20.0 if x >= 0 else (-30.0 if x >= -500 else -200.0)

    def water(self, x, y):
        return 0.0

    def wet(self, x, y, margin=0.0):
        return self.height(x, y) < self.water(x, y) - margin


def test_a_work_spot_in_the_water_moves_to_the_nearest_street_point_with_footing():
    G = Bank()
    assert not jail.footing(-100.0, 0.0, [], {}, G) and jail.footing(100.0, 0.0, [], {}, G)
    paths = [{"id": "t.p", "points": [[-300.0, 0.0], [300.0, 0.0]]}]
    x, y = jail.dry_spot((-300.0, 0.0), paths, [], {}, G)
    assert x >= 0 and abs(x) < 100 and y == 0.0
    assert jail.dry_spot((200.0, 0.0), paths, [], {}, G) == (200.0, 0.0)


def test_only_water_deeper_than_a_wade_needs_a_walkway():
    G = Bank()
    assert not bridges.deep(G, 100.0, 0.0) and not bridges.deep(G, -100.0, 0.0) and bridges.deep(G, -800.0, 0.0)
    assert -30.0 >= 0.0 - WADE and -200.0 < 0.0 - WADE


def test_the_streets_stage_lays_walkways_only_over_a_streets_deep_stretch(monkeypatch):
    calls = []
    monkeypatch.setattr(bridges, "over", lambda pid, pts, k, wb, b, G, rows: calls.append(k) or
                        [{"id": f"br{k}", "base": wb, "kind": "building", "pos": [-800.0, 0.0, 0.0]}])
    paths = [{"id": "t.path.01", "points": [[0.0, 0.0], [-300.0, 0.0]]},        # a ford: waded
             {"id": "t.path.02", "points": [[0.0, 50.0], [-900.0, 50.0]]}]       # deep water: a walkway
    got = bridges.streets("t", paths, [], {"M:ledge": LEDGE}, Bank(), "M:ledge", log=lambda m: None)
    assert calls == [1] and [r["id"] for r in got] == ["br1"]
    assert bridges.streets("t", paths, [], {}, Bank(), None) == []


def test_the_places_own_station_outdoors_is_worked_before_one_added_in_a_room():
    spit = {"key": "S:spit", "edid": "CraftingCookingFireSpit"}
    pot = {"key": "S:pot", "edid": "CraftingCookingPot01"}
    st = SimpleNamespace(ext=[{"id": "t.spit", "base": "S:spit"}], bases={"S:spit": spit, "S:pot": pot},
                         files={"spaces": {"hold": {"refs": [{"id": "t.pot", "base": "S:pot"}]}}})
    added = [{"station": "cooking-pot", "id": "t.pot", "base": "S:pot", "space": "hold", "by": "t.cook"}]
    folk = [{"id": "t.cook", "work": {"space": "hold", "pos": [1, 2, 3]},
             "routine": [{"kind": "work", "at": {"space": "hold", "pos": [1, 2, 3]}},
                         {"kind": "wander", "at": {"space": "hold", "radius": 1024}},
                         {"kind": "sleep", "at": {"space": "exterior", "ref": "t.bed"}}]}]
    found = {"cooking-pot": ["t.pot"]}
    assert stages.outdoor_station(st, "cooking-pot", found, added, folk) == ["t.cook"]
    assert found["cooking-pot"] == ["t.spit"] and added == [] and st.files["spaces"]["hold"]["refs"] == []
    assert folk[0]["work"] == {"space": "exterior", "ref": "t.spit", "radius": 384}
    assert [s["at"].get("ref") for s in folk[0]["routine"]] == ["t.spit", "t.spit", "t.bed"]


def test_a_stop_on_a_deck_is_written_with_its_height_and_one_on_the_ground_without():
    W = walk.Walkable.__new__(walk.Walkable)
    W.zref = lambda x, y: 0.0
    W.found = lambda p: (0, 0.0, 150.0 if p[0] > 0 else 4.0)
    assert W.stood((10.0, 5.0)) == [10.0, 5.0, 150.0]
    assert W.stood((-10.0, 5.0)) == [-10.0, 5.0]
