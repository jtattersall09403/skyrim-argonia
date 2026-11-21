import numpy as np

from tools.places import carrynav as cn
from tools.places.draft.srcnav import carried_tris, carry, edge_report, on_surface

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


FLAT = [{"verts": [[0, 0, 0], [256, 0, 0], [0, 256, 0], [256, 256, 0]], "tris": [[0, 1, 2, 64], [1, 3, 2, 0]]}]


def test_carried_triangles_keep_flags_and_follow_our_patched_ground():
    got = carried_tris(PLACE, FLAT, lambda x, y: 0.0, lambda x, y: 470.0 + 0.1 * (x - 10000), 5000.0)
    assert got["stats"]["kept"] == 2 and got["stats"]["steep"] == 0
    assert [f for _, f, _ in got["tris"]] == [64, 0]               # the source's PREFERRED kept on its triangle
    z = {round(p[0]): p[2] for t, _, _ in got["tris"] for p in t}
    assert z[10256] == 470.0 + 25.6                                # a land row's change summed into the ground


def test_triangle_made_too_steep_by_our_ground_is_dropped_and_listed():
    mound = lambda x, y: 470.0 + (400.0 if x > 10200 else 0.0)    # noqa: E731  a land-brushed mound under one corner
    got = carried_tris(PLACE, FLAT, lambda x, y: 0.0, mound, 5000.0)
    assert got["stats"]["steep"] == 2 and not got["tris"]
    assert all(cn.slope_deg(t) > cn.MAX_SLOPE_DEG for t in got["steep"])
    # the steep triangles become zones: the generator meshes that patch, joined to what is kept
    region = cn.Region(cn.disk((10000, 20000), 2000, 24), [cn.ccw([(p[0], p[1]) for p in t]) for t in got["steep"]])
    gen = {(2, 4): [([(8192 + 256 * i, 16384 + 256 * j, 470.0), (8192 + 256 * (i + 1), 16384 + 256 * j, 470.0),
                      (8192 + 256 * (i + 1), 16384 + 256 * (j + 1), 470.0)], 0)
                    for i in range(16) for j in range(16)]}
    out = cn.build_cells([], gen, region)
    V = np.asarray(out[(2, 4)]["verts"])
    mids = [V[t].mean(axis=0) for t in out[(2, 4)]["tris"]]
    assert any(10000 < m[0] < 10256 and 20000 < m[1] < 20256 for m in mids)


class Deck:
    """A posed piece's walked surface: a flat deck at z over a plan box (shape.Posed.surface_near's contract)."""

    def __init__(self, x0, y0, x1, y1, z):
        self.box, self.z = (x0, y0, x1, y1), z

    def surface_near(self, x, y, z, r, dz):
        x0, y0, x1, y1 = self.box
        return self.z if x0 - r <= x <= x1 + r and y0 - r <= y <= y1 + r and abs(z - self.z) <= dz else None


def test_a_triangle_rests_on_a_piece_by_its_walked_surface_not_its_box():
    deck = Deck(0, 0, 400, 400, 300)
    assert on_surface(deck, [(10, 10, 300), (200, 10, 300), (10, 200, 300)])
    assert not on_surface(deck, [(10, 10, 0), (200, 10, 0), (10, 200, 0)])     # the ground under the deck stays


def test_moved_unit_patch_joining_nothing_falls_back_to_the_generator():
    region = cn.Region(cn.disk((2000, 2000), 1500, 24), [cn.grow([(1800, 1800), (2200, 1800), (2200, 2200), (1800, 2200)])])
    gen = {(0, 0): [([(256 * i, 256 * j, 0.0), (256 * (i + 1), 256 * j, 0.0), (256 * (i + 1), 256 * (j + 1), 0.0)], 0)
                    for i in range(16) for j in range(16)]
                   + [([(256 * i, 256 * j, 0.0), (256 * (i + 1), 256 * (j + 1), 0.0), (256 * i, 256 * (j + 1), 0.0)], 0)
                      for i in range(16) for j in range(16)]}
    boat = [([(1900, 1900, 200.0), (2100, 1900, 200.0), (2100, 2100, 200.0)], 0, 1)]     # a deck in the air: joins nothing
    out, mv = cn.place_cells(boat, gen, region, on_moved=[lambda t: False])
    assert mv == {"moved_kept": 0, "moved_island": 1}
    assert 1 not in out[(0, 0)]["tags"]
    # a unit moved onto a spot whose generated triangle it replaces (resting on its surface there): joined, kept
    ramp = [([(1792, 1792, 0.0), (2048, 1792, 0.0), (2048, 2048, 0.0)], 0, 1)]
    on = lambda t: abs(np.mean([p[0] for p in t]) - 1962.7) < 1 and abs(np.mean([p[1] for p in t]) - 1877.3) < 1  # noqa: E731
    out, mv = cn.place_cells(ramp, gen, region, on_moved=[on])
    assert mv["moved_island"] == 0 and 1 in out[(0, 0)]["tags"]


def test_a_stair_foot_whose_ground_moved_more_than_a_climb_is_meshed_again():
    # two corners on the source's ground, two on a landing 200 up (a stair's run); our ground 50 lower at the foot
    run = [{"verts": [[0, 0, 0], [256, 0, 0], [0, 256, 200], [256, 256, 200]], "tris": [[0, 1, 2, 0], [1, 3, 2, 0]]}]
    got = carried_tris(PLACE, run, lambda x, y: 0.0, lambda x, y: 420.0, 5000.0)
    assert got["stats"]["joints"] == 2 and not got["tris"]          # both triangles hold a moved foot corner
    got = carried_tris(PLACE, run, lambda x, y: 0.0, lambda x, y: 450.0, 5000.0)
    assert got["stats"]["joints"] == 0 and got["stats"]["kept"] == 2   # 20 lower: within a climb, kept
    got = carried_tris(PLACE, run, lambda x, y: 0.0, lambda x, y: 520.0, 5000.0)
    assert got["stats"]["joints"] == 0 and got["stats"]["kept"] == 2   # 50 higher: the ground buries the bottom steps


def test_a_walkway_our_raised_ground_buries_is_meshed_again():
    # a walkway 100 over the source's ground (off it), our ground raised 200 there: buried, dropped and listed
    deck = [{"verts": [[0, 0, 100], [256, 0, 100], [0, 256, 100]], "tris": [[0, 1, 2, 0]]}]
    got = carried_tris(PLACE, deck, lambda x, y: 0.0, lambda x, y: 470.0 + 200.0, 5000.0)
    assert got["stats"]["buried"] == 1 and not got["tris"] and len(got["steep"]) == 1
    got = carried_tris(PLACE, deck, lambda x, y: 0.0, lambda x, y: 470.0 + 90.0, 5000.0)
    assert got["stats"]["buried"] == 0 and got["stats"]["kept"] == 1       # within a climb of our ground: kept
