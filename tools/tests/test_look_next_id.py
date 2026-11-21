"""A hand-placed piece never takes the LOOK id of a row an earlier look session committed."""
from types import SimpleNamespace

from tools.places.look.verbs import next_n


def test_next_n_skips_committed_ids():
    sc = SimpleNamespace(place_id="p", refs={"p.LOOK001PLACE": {}, "p.LOOK002STEPS": {}, "p.LOOK0030000": {}})
    sess: dict = {}
    assert next_n(sc, sess, "PLACE") == 2      # LOOK001PLACE is taken
    assert next_n(sc, sess, "STEPS") == 3      # LOOK003STEPS is free
    copies = {"n": 2}
    assert next_n(sc, copies, "") == 4         # a copy's stem LOOK003 is taken by LOOK0030000


def test_next_n_counts_on_from_the_session():
    sc = SimpleNamespace(place_id="p", refs={})
    sess = {"n": 7}
    assert next_n(sc, sess, "PLACE") == 8
    assert sess["n"] == 8
