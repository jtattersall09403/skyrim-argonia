from tools.places.draft.srcnav import carry, edge_report

PLACE = {"fit": {"pivot": [0.0, 0.0], "anchor": [10000.0, 20000.0], "rot_deg": 0.0}, "wholesale": {"offset": 470.0}}
NAV = [{"verts": [[0, 0, 0], [256, 0, 0], [0, 256, 300], [256, 256, 300]], "tris": [[0, 1, 2, 0], [1, 3, 2, 0]]}]


def test_ground_vertex_follows_our_ground_deck_vertex_keeps_height():
    res = carry(PLACE, NAV, lambda x, y: 0.0, lambda x, y: 500.0, [], 5000.0)
    cl = next(iter(res["cells"].values()))
    zs = sorted({v[2] for v in cl["verts"]})
    assert zs == [500.0, 770.0]          # on ground: our ground (a mound raised it 30); on a deck: source + 470
    assert res["stats"]["kept"] == 2 and edge_report(cl)["tris"] == 2


def test_triangle_under_a_changed_piece_or_outside_is_dropped():
    res = carry(PLACE, NAV, lambda x, y: 0.0, lambda x, y: 470.0, [(10000, 20000, 10150, 20100)], 5000.0)
    assert res["stats"]["under_changed"] == 1 and res["stats"]["kept"] == 1
    res = carry(PLACE, NAV, lambda x, y: 0.0, lambda x, y: 470.0, [], 50.0)
    assert res["stats"]["outside"] == 2
