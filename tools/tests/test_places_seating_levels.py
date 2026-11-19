"""A walked structure with its own flight is seated as one body (seating.levels)."""
from tools.places.draft import seating
from tools.places.seat import seat_all


class Slope:
    """Our ground: rising 1 unit per unit of x (the source's was flat at 0)."""
    def has(self, x, y):
        return True

    def height(self, x, y):
        return x

    def water(self, x, y):
        return None


BASES = {
    "plate": {"model": "keep/ledgemid01.nif", "bounds": [[-128, -128, -16], [128, 128, 0]]},
    "stairs": {"model": "keep/ledgestairs01.nif", "bounds": [[-128, -128, 0], [128, 128, 400]]},
    "wall": {"model": "keep/wall01.nif", "bounds": [[-128, -16, 0], [128, 16, 400]]},
}


def _row(rid, base, x, z, mode, dz):
    return {"id": f"p.{rid}", "src": rid, "base": base, "kind": "building", "pos": [x, 0.0, z], "rot": [0, 0, 0],
            "seat": {"foot": [-128.0, -128.0, 128.0, 128.0], "mode": mode, "dz": dz}}


def test_a_flight_and_its_deck_keep_their_source_heights():
    # source: a flight from the ground (0) up to a yard of two plates at 400
    src = {"s": {"id": "s", "base": "stairs", "pos": [0, 0, 0], "rot": [0, 0, 0]},
           "a": {"id": "a", "base": "plate", "pos": [256, 0, 400], "rot": [0, 0, 0]},
           "b": {"id": "b", "base": "plate", "pos": [512, 0, 400], "rot": [0, 0, 0]},
           "w": {"id": "w", "base": "wall", "pos": [2000, 0, 0], "rot": [0, 0, 0]}}
    rows = [_row("s", "stairs", 0, 0, "ground", 0.0), _row("a", "plate", 256, 400, "above", 400.0),
            _row("b", "plate", 512, 400, "above", 400.0), _row("w", "wall", 2000, 0, "ground", 0.0)]
    g = Slope()
    assert seating.levels(rows, src, BASES, g) == 2
    seat_all(rows, g)
    z = {r["src"]: r["pos"][2] for r in rows}
    # the flight's foot meets our ground at its lowest corner; the yard stays level at its top
    assert z["s"] == -128.0
    assert z["a"] == z["b"] == z["s"] + 400
    assert rows[1]["seat"]["mode"] == "on" and rows[1]["seat"]["on"] == "p.s"
    # a piece that touches no walked structure keeps its own rule
    assert rows[3]["seat"]["mode"] == "ground"


def test_a_laid_flight_moves_with_the_deck_that_carries_it():
    deck = {"id": "d", "pos": [0, 0, 300.0], "seat": {"mode": "ground", "dz": 0}}
    flight = {"id": "f", "pos": [0, 0, 250.0], "seat": {"mode": "free", "carrier": ["x", "d"]}}
    other = {"id": "o", "pos": [0, 0, 10.0], "seat": {"mode": "free"}}
    was = {"d": 380.0, "f": 250.0, "o": 10.0}
    assert seating.carry([deck, flight, other], was) == 1
    assert flight["pos"][2] == 170.0 and other["pos"][2] == 10.0


def test_decks_without_a_flight_keep_their_own_rule():
    src = {"a": {"id": "a", "base": "plate", "pos": [0, 0, 400], "rot": [0, 0, 0]},
           "b": {"id": "b", "base": "plate", "pos": [256, 0, 400], "rot": [0, 0, 0]}}
    rows = [_row("a", "plate", 0, 400, "above", 400.0), _row("b", "plate", 256, 400, "above", 400.0)]
    assert seating.levels(rows, src, BASES, Slope()) == 0
