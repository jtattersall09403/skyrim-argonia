"""The derive's trader loop keeps its give `g` through every weapon and armour pick: a walrus `g :=` in a generator
once rebound it to the picked item, and `g.give_kind_id` then failed for every place with a trader."""
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "places" / "stock" / "derive.py"


def test_no_walrus_rebinds_the_give():
    assert "(g := " not in SRC.read_text()
